from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = None
    avatar: Optional[str] = None
    preferred_resource_type: Optional[str] = Field(None, description="Video, Article, Practice, Mixed")
    old_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    preferred_resource_type: Optional[str] = "Mixed"
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
