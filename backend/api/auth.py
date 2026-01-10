"""Authentication endpoints - login, register, JWT handling."""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.hash import bcrypt
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.models import Customer

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None
    favorite_genres: list[str] = []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    favorite_genres: list[str]
    shipping_address: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hash(password)


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Customer:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Customer).where(Customer.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db)
) -> Optional[Customer]:
    """Get the current user if authenticated, otherwise return None."""
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(Customer).where(Customer.email == email))
    return result.scalar_one_or_none()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    result = await db.execute(
        select(Customer).where(Customer.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create token
    access_token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "favorite_genres": user.favorite_genres or [],
            "shipping_address": user.shipping_address,
        }
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if email already exists
    result = await db.execute(
        select(Customer).where(Customer.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = Customer(
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
        phone=request.phone,
        favorite_genres=request.favorite_genres,
        last_login=datetime.utcnow(),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create token
    access_token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "favorite_genres": user.favorite_genres or [],
            "shipping_address": user.shipping_address,
        }
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Customer = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        favorite_genres=current_user.favorite_genres or [],
        shipping_address=current_user.shipping_address,
        created_at=current_user.created_at,
    )


@router.get("/demo-accounts")
async def get_demo_accounts():
    """Get list of demo accounts for quick login."""
    from data.seed_users import USER_PROFILES

    return [
        {
            "email": p["email"],
            "name": p["name"],
            "description": p["description"],
            "preferences": p["favorite_genres"],
        }
        for p in USER_PROFILES
    ]
