"""Shopping cart endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.database import get_db
from data.models import CartItem, Book, Customer
from api.auth import get_current_user

router = APIRouter()


class CartItemRequest(BaseModel):
    book_id: int
    quantity: int = 1


class CartItemResponse(BaseModel):
    id: int
    book_id: int
    book_title: str
    book_author: str
    book_cover: Optional[str]
    book_price: float
    quantity: int
    subtotal: float


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    subtotal: float
    shipping: float
    total: float


def calculate_shipping(subtotal: float) -> float:
    """Calculate shipping cost. Free for orders over $35."""
    return 0.0 if subtotal >= 35 else 4.99


@router.get("", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get current user's cart."""
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.book))
        .where(CartItem.customer_id == current_user.id)
    )
    cart_items = result.scalars().all()

    items = []
    subtotal = 0.0

    for item in cart_items:
        item_subtotal = item.book.price * item.quantity
        subtotal += item_subtotal
        items.append(CartItemResponse(
            id=item.id,
            book_id=item.book.id,
            book_title=item.book.title,
            book_author=item.book.author,
            book_cover=item.book.cover_image,
            book_price=item.book.price,
            quantity=item.quantity,
            subtotal=round(item_subtotal, 2),
        ))

    shipping = calculate_shipping(subtotal)

    return CartResponse(
        items=items,
        total_items=sum(item.quantity for item in cart_items),
        subtotal=round(subtotal, 2),
        shipping=shipping,
        total=round(subtotal + shipping, 2),
    )


@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: CartItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Add a book to cart."""
    # Verify book exists and is in stock
    result = await db.execute(select(Book).where(Book.id == request.book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book.stock_quantity < request.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {book.stock_quantity} copies available"
        )

    # Check if item already in cart
    result = await db.execute(
        select(CartItem).where(
            CartItem.customer_id == current_user.id,
            CartItem.book_id == request.book_id,
        )
    )
    existing_item = result.scalar_one_or_none()

    if existing_item:
        # Update quantity
        new_quantity = existing_item.quantity + request.quantity
        if new_quantity > book.stock_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Only {book.stock_quantity} copies available"
            )
        existing_item.quantity = new_quantity
    else:
        # Add new item
        cart_item = CartItem(
            customer_id=current_user.id,
            book_id=request.book_id,
            quantity=request.quantity,
        )
        db.add(cart_item)

    await db.commit()

    # Return updated cart
    return await get_cart(db=db, current_user=current_user)


@router.put("/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: int,
    request: CartItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Update cart item quantity."""
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.book))
        .where(CartItem.id == item_id, CartItem.customer_id == current_user.id)
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if request.quantity <= 0:
        # Remove item
        await db.delete(cart_item)
    else:
        if request.quantity > cart_item.book.stock_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Only {cart_item.book.stock_quantity} copies available"
            )
        cart_item.quantity = request.quantity

    await db.commit()

    return await get_cart(db=db, current_user=current_user)


@router.delete("/{item_id}", response_model=CartResponse)
async def remove_from_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Remove item from cart."""
    result = await db.execute(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.customer_id == current_user.id,
        )
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()

    return await get_cart(db=db, current_user=current_user)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Clear all items from cart."""
    await db.execute(
        delete(CartItem).where(CartItem.customer_id == current_user.id)
    )
    await db.commit()

    return CartResponse(
        items=[],
        total_items=0,
        subtotal=0.0,
        shipping=0.0,
        total=0.0,
    )
