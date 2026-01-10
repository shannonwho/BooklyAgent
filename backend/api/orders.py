"""Order management endpoints."""
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.database import get_db
from data.models import (
    Order, OrderItem, OrderStatus, CartItem, Book, Customer
)
from api.auth import get_current_user

router = APIRouter()


class OrderItemResponse(BaseModel):
    id: int
    book_id: int
    book_title: str
    book_author: str
    book_cover: Optional[str]
    quantity: int
    price_per_unit: float
    subtotal: float


class OrderResponse(BaseModel):
    id: int
    order_number: str
    status: str
    total_amount: float
    subtotal: float
    shipping_cost: float
    tax: float
    shipping_address: dict
    shipping_method: str
    tracking_number: Optional[str]
    carrier: Optional[str]
    estimated_delivery: Optional[datetime]
    items: list[OrderItemResponse]
    order_date: datetime
    shipped_date: Optional[datetime]
    delivered_date: Optional[datetime]
    return_requested: bool
    return_approved: bool
    refund_amount: float


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int


class CheckoutRequest(BaseModel):
    shipping_address: dict
    shipping_method: str = "standard"


class CheckoutResponse(BaseModel):
    order_number: str
    total_amount: float
    estimated_delivery: datetime


def generate_order_number() -> str:
    """Generate a unique order number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"ORD-{timestamp}-{random_suffix}"


def generate_tracking_number() -> tuple[str, str]:
    """Generate a realistic tracking number."""
    carriers = ["USPS", "FedEx", "UPS"]
    carrier = random.choice(carriers)
    tracking = "".join([str(random.randint(0, 9)) for _ in range(12)])
    return tracking, carrier


def calculate_shipping_cost(method: str, subtotal: float) -> float:
    """Calculate shipping cost based on method."""
    if subtotal >= 35 and method == "standard":
        return 0.0

    costs = {
        "standard": 4.99,
        "express": 9.99,
        "overnight": 19.99,
    }
    return costs.get(method, 4.99)


def calculate_estimated_delivery(method: str) -> datetime:
    """Calculate estimated delivery date."""
    days = {
        "standard": random.randint(5, 7),
        "express": random.randint(2, 3),
        "overnight": 1,
    }
    return datetime.utcnow() + timedelta(days=days.get(method, 5))


@router.get("", response_model=OrderListResponse)
async def get_orders(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get all orders for current user."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.book))
        .where(Order.customer_id == current_user.id)
        .order_by(Order.order_date.desc())
    )
    orders = result.scalars().all()

    order_responses = []
    for order in orders:
        items = [
            OrderItemResponse(
                id=item.id,
                book_id=item.book.id,
                book_title=item.book.title,
                book_author=item.book.author,
                book_cover=item.book.cover_image,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                subtotal=round(item.quantity * item.price_per_unit, 2),
            )
            for item in order.items
        ]

        # Calculate subtotal from items
        subtotal = sum(item.subtotal for item in items)
        # Estimate shipping and tax from total
        shipping_cost = calculate_shipping_cost(order.shipping_method, subtotal)
        tax = round(order.total_amount - subtotal - shipping_cost, 2)
        if tax < 0:
            tax = round(subtotal * 0.08, 2)  # Default 8% tax estimate

        order_responses.append(OrderResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status.value,
            total_amount=order.total_amount,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            shipping_address=order.shipping_address,
            shipping_method=order.shipping_method,
            tracking_number=order.tracking_number,
            carrier=order.carrier,
            estimated_delivery=order.estimated_delivery,
            items=items,
            order_date=order.order_date,
            shipped_date=order.shipped_date,
            delivered_date=order.delivered_date,
            return_requested=order.return_requested,
            return_approved=order.return_approved,
            refund_amount=order.refund_amount,
        ))

    return OrderListResponse(orders=order_responses, total=len(order_responses))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get a specific order by ID."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.book))
        .where(Order.id == order_id, Order.customer_id == current_user.id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [
        OrderItemResponse(
            id=item.id,
            book_id=item.book.id,
            book_title=item.book.title,
            book_author=item.book.author,
            book_cover=item.book.cover_image,
            quantity=item.quantity,
            price_per_unit=item.price_per_unit,
            subtotal=round(item.quantity * item.price_per_unit, 2),
        )
        for item in order.items
    ]

    # Calculate subtotal from items
    subtotal = sum(item.subtotal for item in items)
    # Estimate shipping and tax from total
    shipping_cost = calculate_shipping_cost(order.shipping_method, subtotal)
    tax = round(order.total_amount - subtotal - shipping_cost, 2)
    if tax < 0:
        tax = round(subtotal * 0.08, 2)  # Default 8% tax estimate

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status.value,
        total_amount=order.total_amount,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        shipping_address=order.shipping_address,
        shipping_method=order.shipping_method,
        tracking_number=order.tracking_number,
        carrier=order.carrier,
        estimated_delivery=order.estimated_delivery,
        items=items,
        order_date=order.order_date,
        shipped_date=order.shipped_date,
        delivered_date=order.delivered_date,
        return_requested=order.return_requested,
        return_approved=order.return_approved,
        refund_amount=order.refund_amount,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    request: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Create a new order from cart items."""
    # Get cart items
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.book))
        .where(CartItem.customer_id == current_user.id)
    )
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate totals
    subtotal = sum(item.book.price * item.quantity for item in cart_items)
    shipping = calculate_shipping_cost(request.shipping_method, subtotal)
    total = round(subtotal + shipping, 2)

    # Verify stock availability
    for item in cart_items:
        if item.quantity > item.book.stock_quantity:
            raise HTTPException(
                status_code=400,
                detail=f"'{item.book.title}' only has {item.book.stock_quantity} copies available"
            )

    # Generate order info
    order_number = generate_order_number()
    tracking_number, carrier = generate_tracking_number()
    estimated_delivery = calculate_estimated_delivery(request.shipping_method)

    # Create order
    order = Order(
        order_number=order_number,
        customer_id=current_user.id,
        status=OrderStatus.PROCESSING,
        total_amount=total,
        shipping_address=request.shipping_address,
        shipping_method=request.shipping_method,
        tracking_number=tracking_number,
        carrier=carrier,
        estimated_delivery=estimated_delivery,
        order_date=datetime.utcnow(),
    )
    db.add(order)
    await db.flush()

    # Create order items and update stock
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            book_id=cart_item.book.id,
            quantity=cart_item.quantity,
            price_per_unit=cart_item.book.price,
        )
        db.add(order_item)

        # Update stock
        cart_item.book.stock_quantity -= cart_item.quantity

    # Clear cart
    await db.execute(
        delete(CartItem).where(CartItem.customer_id == current_user.id)
    )

    await db.commit()

    return CheckoutResponse(
        order_number=order_number,
        total_amount=total,
        estimated_delivery=estimated_delivery,
    )


@router.get("/by-number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get a specific order by order number."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.book))
        .where(
            Order.order_number == order_number,
            Order.customer_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [
        OrderItemResponse(
            id=item.id,
            book_id=item.book.id,
            book_title=item.book.title,
            book_author=item.book.author,
            book_cover=item.book.cover_image,
            quantity=item.quantity,
            price_per_unit=item.price_per_unit,
            subtotal=round(item.quantity * item.price_per_unit, 2),
        )
        for item in order.items
    ]

    # Calculate subtotal from items
    subtotal = sum(item.subtotal for item in items)
    # Estimate shipping and tax from total
    shipping_cost = calculate_shipping_cost(order.shipping_method, subtotal)
    tax = round(order.total_amount - subtotal - shipping_cost, 2)
    if tax < 0:
        tax = round(subtotal * 0.08, 2)  # Default 8% tax estimate

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status.value,
        total_amount=order.total_amount,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax=tax,
        shipping_address=order.shipping_address,
        shipping_method=order.shipping_method,
        tracking_number=order.tracking_number,
        carrier=order.carrier,
        estimated_delivery=order.estimated_delivery,
        items=items,
        order_date=order.order_date,
        shipped_date=order.shipped_date,
        delivered_date=order.delivered_date,
        return_requested=order.return_requested,
        return_approved=order.return_approved,
        refund_amount=order.refund_amount,
    )
