from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User

# Optional OAuth2 scheme for swagger docs
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode("utf-8")
        else:
            hashed_bytes = hashed_password
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # bcrypt salt generation
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None

def extract_token_from_request(request: Request, header_token: Optional[str] = None) -> Optional[str]:
    # 1. Check Bearer Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    if isinstance(header_token, str) and header_token.strip():
        return header_token.strip()
    # 2. Check HttpOnly cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token and isinstance(cookie_token, str):
        if cookie_token.startswith("Bearer "):
            return cookie_token[7:].strip()
        return cookie_token
    return None

def get_current_user_optional(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    raw_token = extract_token_from_request(request, token)
    if not raw_token or not isinstance(raw_token, str):
        return None
    payload = decode_access_token(raw_token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # Ensure db session
    session = db
    if session is None or not hasattr(session, "query"):
        session = next(get_db())

    user = session.query(User).filter(User.id == int(user_id)).first()
    return user

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    user = get_current_user_optional(request, token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user
