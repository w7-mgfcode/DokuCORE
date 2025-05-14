from pydantic import BaseModel, EmailStr
from typing import Optional, List


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model for decoded JWT tokens."""
    username: Optional[str] = None
    scopes: List[str] = []


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: List[str] = []


class UserInDB(User):
    """User model as stored in the database with hashed password."""
    hashed_password: str


class UserCreate(BaseModel):
    """User creation model."""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    scopes: List[str] = ["documents:read", "tasks:read"]


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str