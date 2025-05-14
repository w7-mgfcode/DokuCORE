import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from ..models.auth import TokenData, User, UserInDB
from ..utils.db import get_db_connection
from ..utils.config import config

logger = logging.getLogger(__name__)

# Constants for JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "insecure-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_TOKEN_EXPIRE_MINUTES", 30))

# OAuth2 password bearer for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes={
        "documents:read": "Read documents",
        "documents:write": "Create and update documents",
        "tasks:read": "Read tasks",
        "tasks:write": "Create and update tasks",
        "users:read": "Read user information",
        "users:write": "Create and update users",
    }
)

# Password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password (str): Plain text password.
        hashed_password (str): Hashed password.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password (str): Plain text password.
        
    Returns:
        str: Hashed password.
    """
    return pwd_context.hash(password)


def get_user_from_db(username: str) -> Optional[UserInDB]:
    """
    Get a user from the database.
    
    Args:
        username (str): Username to look up.
        
    Returns:
        Optional[UserInDB]: User if found, None otherwise.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create the users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    hashed_password TEXT NOT NULL,
                    disabled BOOLEAN DEFAULT FALSE,
                    scopes TEXT[] DEFAULT '{documents:read,tasks:read}'
                )
            """)
            conn.commit()
            cursor.close()
            conn.close()
            return None
        
        # Query the user
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_row:
            return None
            
        # Convert row to UserInDB model
        # Assuming the column order is: id, username, email, full_name, hashed_password, disabled, scopes
        return UserInDB(
            username=user_row[1],
            email=user_row[2],
            full_name=user_row[3],
            hashed_password=user_row[4],
            disabled=user_row[5],
            scopes=user_row[6]
        )
    except Exception as e:
        logger.error(f"Error getting user from database: {str(e)}")
        return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user with username and password.
    
    Args:
        username (str): Username to authenticate.
        password (str): Password to verify.
        
    Returns:
        Optional[UserInDB]: User if authentication is successful, None otherwise.
    """
    user = get_user_from_db(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data (Dict[str, Any]): Data to encode in the token.
        expires_delta (Optional[timedelta]): Token expiration time.
        
    Returns:
        str: JWT token.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_user(username: str, email: str, password: str, full_name: Optional[str] = None, scopes: List[str] = None) -> Optional[User]:
    """
    Create a new user in the database.
    
    Args:
        username (str): Username for the new user.
        email (str): Email for the new user.
        password (str): Password for the new user.
        full_name (Optional[str]): Full name for the new user.
        scopes (List[str]): Scopes for the new user.
        
    Returns:
        Optional[User]: Created user if successful, None otherwise.
    """
    try:
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Set default scopes if not provided
        if scopes is None:
            scopes = ["documents:read", "tasks:read"]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if the users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create the users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    hashed_password TEXT NOT NULL,
                    disabled BOOLEAN DEFAULT FALSE,
                    scopes TEXT[] DEFAULT '{documents:read,tasks:read}'
                )
            """)
        
        # Insert the new user
        cursor.execute(
            """
            INSERT INTO users (username, email, full_name, hashed_password, disabled, scopes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, username, email, full_name, disabled, scopes
            """,
            (username, email, full_name, hashed_password, False, scopes)
        )
        
        user_row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not user_row:
            return None
            
        # Return the created user
        return User(
            username=user_row[1],
            email=user_row[2],
            full_name=user_row[3],
            disabled=user_row[4],
            scopes=user_row[5]
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None


async def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        security_scopes (SecurityScopes): Required scopes for the endpoint.
        token (str): JWT token from the Authorization header.
        
    Returns:
        User: The authenticated user.
        
    Raises:
        HTTPException: If authentication fails.
    """
    if security_scopes.scopes:
        authenticate_value = f"Bearer scope={security_scopes.scope_str}"
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value}
    )
    
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes)
    except (JWTError, ValidationError):
        raise credentials_exception
        
    # Get the user from the database
    user = get_user_from_db(token_data.username)
    
    if user is None:
        raise credentials_exception
        
    # Check if the user is disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": authenticate_value}
        )
    
    # Check scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: {scope}",
                headers={"WWW-Authenticate": f"{authenticate_value} scope={security_scopes.scope_str}"}
            )
    
    # Convert UserInDB to User (to remove the hashed_password)
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
        scopes=user.scopes
    )


async def get_current_active_user(current_user: User = Security(get_current_user, scopes=[])) -> User:
    """
    Get the current active user.
    
    Args:
        current_user (User): The current authenticated user.
        
    Returns:
        User: The current authenticated active user.
        
    Raises:
        HTTPException: If the user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user