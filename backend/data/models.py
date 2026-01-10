"""SQLAlchemy database models."""
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime,
    ForeignKey, Enum, JSON, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base


# Enums
class OrderStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class Genre(str, PyEnum):
    FICTION = "Fiction"
    SCIFI = "Sci-Fi"
    MYSTERY = "Mystery"
    ROMANCE = "Romance"
    SELF_HELP = "Self-Help"
    BIOGRAPHY = "Biography"
    HISTORY = "History"
    BUSINESS = "Business"
    FANTASY = "Fantasy"
    THRILLER = "Thriller"


class TicketStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Association table for customer favorite genres
customer_genres = Table(
    "customer_genres",
    Base.metadata,
    Column("customer_id", Integer, ForeignKey("customers.id"), primary_key=True),
    Column("genre", Enum(Genre), primary_key=True),
)


class Book(Base):
    """Book catalog model."""
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    isbn: Mapped[str] = mapped_column(String(17), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[str] = mapped_column(String(255), index=True)
    genre: Mapped[Genre] = mapped_column(Enum(Genre), index=True)
    price: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    cover_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    num_reviews: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=200)
    publication_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="book")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="book")


class Customer(Base):
    """Customer account model."""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Preferences stored as JSON array of genre strings
    favorite_genres: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Shipping address (simplified as JSON for demo)
    shipping_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    newsletter_subscribed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="customer")
    support_tickets: Mapped[List["SupportTicket"]] = relationship(back_populates="customer")


class Order(Base):
    """Customer order model."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount: Mapped[float] = mapped_column(Float)

    # Shipping info
    shipping_address: Mapped[dict] = mapped_column(JSON)
    shipping_method: Mapped[str] = mapped_column(String(50), default="standard")
    tracking_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    carrier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Return/refund info
    return_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    return_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    return_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_amount: Mapped[float] = mapped_column(Float, default=0.0)
    refund_processed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    shipped_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Individual item in an order."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"))
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_per_unit: Mapped[float] = mapped_column(Float)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    book: Mapped["Book"] = relationship(back_populates="order_items")


class CartItem(Base):
    """Shopping cart item."""
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"))
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="cart_items")
    book: Mapped["Book"] = relationship(back_populates="cart_items")


class Policy(Base):
    """Company policy documents for agent grounding."""
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_type: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SupportTicket(Base):
    """Customer support ticket."""
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"))
    category: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority), default=TicketPriority.MEDIUM)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="support_tickets")
