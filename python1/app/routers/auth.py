from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token
from app.templating import render_template
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_user_optional
)

router = APIRouter(tags=["Authentication"])

# ----------------- HTML Pages -----------------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db=db)
    if current_user:
        if current_user.role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return render_template(request, "login.html", {"user": None, "error": None})

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db=db)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return render_template(request, "register.html", {"user": None, "error": None})

@router.post("/auth/login")
def login_form_post(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return render_template(
            request,
            "login.html",
            {"user": None, "error": "Invalid email or password. Please try again."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})

    # Redirect to appropriate dashboard
    redirect_url = "/admin/dashboard" if user.role == "admin" else "/dashboard"
    redirect_res = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    redirect_res.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return redirect_res

@router.post("/auth/register")
def register_form_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return render_template(
            request,
            "register.html",
            {"user": None, "error": "Passwords do not match."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 6:
        return render_template(
            request,
            "register.html",
            {"user": None, "error": "Password must be at least 6 characters long."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    cleaned_email = email.strip().lower()
    existing_user = db.query(User).filter(User.email == cleaned_email).first()
    if existing_user:
        return render_template(
            request,
            "register.html",
            {"user": None, "error": "An account with this email already exists."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    user = User(
        name=name.strip(),
        email=cleaned_email,
        password_hash=get_password_hash(password),
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue token and log in directly
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    redirect_res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    redirect_res.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return redirect_res

@router.get("/logout")
def logout_page():
    redirect_res = RedirectResponse(url="/login?logged_out=1", status_code=status.HTTP_303_SEE_OTHER)
    redirect_res.delete_cookie(key="access_token")
    return redirect_res

# ----------------- REST API Endpoints -----------------

@router.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def api_register(data: UserRegister, db: Session = Depends(get_db)):
    cleaned_email = data.email.strip().lower()
    existing = db.query(User).filter(User.email == cleaned_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        name=data.name.strip(),
        email=cleaned_email,
        password_hash=get_password_hash(data.password),
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/api/auth/login", response_model=Token)
def api_login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    cleaned_email = data.email.strip().lower()
    user = db.query(User).filter(User.email == cleaned_email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/api/auth/me", response_model=UserResponse)
def api_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/api/auth/logout")
def api_logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}
