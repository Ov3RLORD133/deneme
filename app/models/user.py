"""
User Model - Authentication & Authorization

Stores operator credentials for accessing the KeyChaser dashboard and API.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field

from app.core.database import Base


class User(Base):
    """
    User database model for authentication.
    
    Stores operator credentials with role-based access control.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


# Pydantic Schemas

class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8, max_length=100)


class UserRead(UserBase):
    """Schema for reading user data (excludes password)"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data"""
    username: str | None = None
