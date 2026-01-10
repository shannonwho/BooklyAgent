"""User profile management endpoints."""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.models import Customer
from api.auth import get_current_user, get_password_hash, verify_password

router = APIRouter()


class ProfileResponse(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str]
    favorite_genres: list[str]
    shipping_address: Optional[dict]
    newsletter_subscribed: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    favorite_genres: Optional[list[str]] = None
    shipping_address: Optional[dict] = None
    newsletter_subscribed: Optional[bool] = None


class UpdateEmailRequest(BaseModel):
    new_email: EmailStr
    password: str


class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: Customer = Depends(get_current_user)):
    """Get current user's profile."""
    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        favorite_genres=current_user.favorite_genres or [],
        shipping_address=current_user.shipping_address,
        newsletter_subscribed=current_user.newsletter_subscribed,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Update current user's profile."""
    if request.name is not None:
        current_user.name = request.name

    if request.phone is not None:
        current_user.phone = request.phone

    if request.favorite_genres is not None:
        current_user.favorite_genres = request.favorite_genres

    if request.shipping_address is not None:
        current_user.shipping_address = request.shipping_address

    if request.newsletter_subscribed is not None:
        current_user.newsletter_subscribed = request.newsletter_subscribed

    await db.commit()
    await db.refresh(current_user)

    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        favorite_genres=current_user.favorite_genres or [],
        shipping_address=current_user.shipping_address,
        newsletter_subscribed=current_user.newsletter_subscribed,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.put("/email", response_model=ProfileResponse)
async def update_email(
    request: UpdateEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Update user's email address."""
    # Verify password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    # Check if new email is already in use
    result = await db.execute(
        select(Customer).where(Customer.email == request.new_email)
    )
    existing = result.scalar_one_or_none()

    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=400, detail="Email already in use")

    current_user.email = request.new_email
    await db.commit()
    await db.refresh(current_user)

    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        phone=current_user.phone,
        favorite_genres=current_user.favorite_genres or [],
        shipping_address=current_user.shipping_address,
        newsletter_subscribed=current_user.newsletter_subscribed,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.put("/password")
async def update_password(
    request: UpdatePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Update user's password."""
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Update password
    current_user.password_hash = get_password_hash(request.new_password)
    await db.commit()

    return {"message": "Password updated successfully"}


@router.get("/preferences")
async def get_preferences(current_user: Customer = Depends(get_current_user)):
    """Get user's reading preferences."""
    return {
        "favorite_genres": current_user.favorite_genres or [],
        "newsletter_subscribed": current_user.newsletter_subscribed,
    }


@router.put("/preferences")
async def update_preferences(
    favorite_genres: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Update user's reading preferences."""
    current_user.favorite_genres = favorite_genres
    await db.commit()

    return {
        "favorite_genres": current_user.favorite_genres,
        "message": "Preferences updated successfully",
    }
