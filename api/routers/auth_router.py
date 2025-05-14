import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm

from ..models.auth import Token, User, UserCreate, UserInDB
from ..services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    create_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get an access token for authentication.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Form data with username and password.
        
    Returns:
        Token: Access token for authentication.
        
    Raises:
        HTTPException: If authentication fails.
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users", response_model=User)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    
    Args:
        user_data (UserCreate): User data for registration.
        
    Returns:
        User: Created user.
        
    Raises:
        HTTPException: If user creation fails.
    """
    # Create the user
    user = create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        scopes=user_data.scopes
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
        
    return user


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Security(get_current_active_user, scopes=["users:read"])):
    """
    Get the current user.
    
    Args:
        current_user (User): The current authenticated user.
        
    Returns:
        User: The current user.
    """
    return current_user


@router.get("/users/me/items")
async def read_own_items(current_user: User = Security(get_current_active_user, scopes=["documents:read"])):
    """
    Get the current user's items.
    
    Args:
        current_user (User): The current authenticated user.
        
    Returns:
        dict: The current user's items.
    """
    return {"owner": current_user.username, "items": []}