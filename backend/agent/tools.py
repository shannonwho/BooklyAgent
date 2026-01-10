"""Tool definitions and execution for the customer support agent."""
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from data.models import (
    Customer, Order, OrderItem, Book, Policy, SupportTicket,
    OrderStatus, TicketStatus, TicketPriority, Genre
)

# Tool definitions for Claude
TOOLS = [
    {
        "name": "get_order_status",
        "description": "Retrieves the current status of a customer's order including items, shipping info, and tracking. Use this when a customer asks about their order status, shipping updates, or delivery information. Requires either order_id or customer email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order number (e.g., 'ORD-2024-00001')"
                },
                "email": {
                    "type": "string",
                    "description": "Customer's email address for verification"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_orders",
        "description": "Searches for orders based on customer email. Use this when the customer doesn't have their order ID or wants to see all their orders. Returns a list of orders.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer's email address"
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "get_customer_info",
        "description": "Retrieves customer account information including order history summary and preferences. Use this to personalize responses and understand the customer's context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer's email address"
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "initiate_return",
        "description": "Starts the return process for an order. IMPORTANT: Only use after confirming with the customer that they want to proceed. Checks if order is eligible for return (within 30 days, not already returned).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order number to return"
                },
                "reason": {
                    "type": "string",
                    "description": "Customer's reason for return",
                    "enum": ["damaged", "wrong_item", "not_as_described", "no_longer_needed", "other"]
                },
                "email": {
                    "type": "string",
                    "description": "Customer email for verification"
                }
            },
            "required": ["order_id", "reason", "email"]
        }
    },
    {
        "name": "get_policy_info",
        "description": "Retrieves official company policy information. ALWAYS use this tool instead of general knowledge when asked about policies. This ensures accuracy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_type": {
                    "type": "string",
                    "description": "Type of policy to retrieve",
                    "enum": ["return", "refund", "shipping", "privacy", "payment", "account"]
                }
            },
            "required": ["policy_type"]
        }
    },
    {
        "name": "get_recommendations",
        "description": "Gets personalized book recommendations based on customer's order history and stated preferences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer's email for personalized recommendations"
                },
                "genre": {
                    "type": "string",
                    "description": "Optional genre filter"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of recommendations (default 5)"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_books",
        "description": "Searches the book catalog by title, author, or keyword. Use when customers ask about book availability.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (title, author, keyword)"
                },
                "genre": {
                    "type": "string",
                    "description": "Optional genre filter"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_support_ticket",
        "description": "Creates a support ticket for issues that require human follow-up. Use when you cannot resolve the issue or the customer needs escalation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer's email"
                },
                "category": {
                    "type": "string",
                    "enum": ["order", "billing", "shipping", "product", "account", "other"]
                },
                "subject": {
                    "type": "string",
                    "description": "Brief subject line"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the issue"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Priority level"
                }
            },
            "required": ["email", "category", "subject", "description"]
        }
    },
]


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    db: AsyncSession
) -> dict[str, Any]:
    """Execute a tool and return the result."""

    if tool_name == "get_order_status":
        return await _get_order_status(tool_input, db)
    elif tool_name == "search_orders":
        return await _search_orders(tool_input, db)
    elif tool_name == "get_customer_info":
        return await _get_customer_info(tool_input, db)
    elif tool_name == "initiate_return":
        return await _initiate_return(tool_input, db)
    elif tool_name == "get_policy_info":
        return await _get_policy_info(tool_input, db)
    elif tool_name == "get_recommendations":
        return await _get_recommendations(tool_input, db)
    elif tool_name == "search_books":
        return await _search_books(tool_input, db)
    elif tool_name == "create_support_ticket":
        return await _create_support_ticket(tool_input, db)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def _get_order_status(params: dict, db: AsyncSession) -> dict:
    """Get order status by order ID or email."""
    order_id = params.get("order_id")
    email = params.get("email")

    if not order_id and not email:
        return {"error": "Please provide either order_id or email"}

    query = select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.book)
    )

    if order_id:
        query = query.where(Order.order_number == order_id)

    result = await db.execute(query)
    order = result.scalar_one_or_none()

    if not order:
        return {"error": f"Order not found. Please verify the order number."}

    # Verify email matches if provided
    customer_result = await db.execute(
        select(Customer).where(Customer.id == order.customer_id)
    )
    customer = customer_result.scalar_one_or_none()

    if email and customer and customer.email.lower() != email.lower():
        return {"error": "Email does not match this order. Please verify your information."}

    items = [
        {
            "title": item.book.title,
            "author": item.book.author,
            "quantity": item.quantity,
            "price": item.price_per_unit,
        }
        for item in order.items
    ]

    return {
        "order_number": order.order_number,
        "status": order.status.value,
        "total_amount": order.total_amount,
        "order_date": order.order_date.strftime("%B %d, %Y"),
        "items": items,
        "shipping_method": order.shipping_method,
        "tracking_number": order.tracking_number,
        "carrier": order.carrier,
        "estimated_delivery": order.estimated_delivery.strftime("%B %d, %Y") if order.estimated_delivery else None,
        "shipped_date": order.shipped_date.strftime("%B %d, %Y") if order.shipped_date else None,
        "delivered_date": order.delivered_date.strftime("%B %d, %Y") if order.delivered_date else None,
        "return_requested": order.return_requested,
        "return_approved": order.return_approved,
    }


async def _search_orders(params: dict, db: AsyncSession) -> dict:
    """Search orders by customer email."""
    email = params.get("email")

    if not email:
        return {"error": "Email is required to search orders"}

    # Find customer
    customer_result = await db.execute(
        select(Customer).where(Customer.email == email)
    )
    customer = customer_result.scalar_one_or_none()

    if not customer:
        return {"error": f"No account found with email {email}"}

    # Get orders
    orders_result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.book))
        .where(Order.customer_id == customer.id)
        .order_by(Order.order_date.desc())
    )
    orders = orders_result.scalars().all()

    if not orders:
        return {"message": "No orders found for this account.", "orders": []}

    orders_list = []
    for order in orders:
        items_summary = ", ".join([
            f"'{item.book.title}'" for item in order.items[:3]
        ])
        if len(order.items) > 3:
            items_summary += f" and {len(order.items) - 3} more"

        orders_list.append({
            "order_number": order.order_number,
            "status": order.status.value,
            "order_date": order.order_date.strftime("%B %d, %Y"),
            "total_amount": order.total_amount,
            "items_summary": items_summary,
            "item_count": len(order.items),
        })

    return {
        "customer_name": customer.name,
        "orders": orders_list,
        "total_orders": len(orders_list),
    }


async def _get_customer_info(params: dict, db: AsyncSession) -> dict:
    """Get customer information."""
    email = params.get("email")

    if not email:
        return {"error": "Email is required"}

    result = await db.execute(
        select(Customer).where(Customer.email == email)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        return {"error": f"No account found with email {email}"}

    # Get order count
    orders_result = await db.execute(
        select(Order).where(Order.customer_id == customer.id)
    )
    orders = orders_result.scalars().all()

    return {
        "name": customer.name,
        "email": customer.email,
        "member_since": customer.created_at.strftime("%B %Y"),
        "favorite_genres": customer.favorite_genres or [],
        "total_orders": len(orders),
        "has_shipping_address": customer.shipping_address is not None,
    }


async def _initiate_return(params: dict, db: AsyncSession) -> dict:
    """Initiate a return for an order."""
    order_id = params.get("order_id")
    reason = params.get("reason")
    email = params.get("email")

    if not all([order_id, reason, email]):
        return {"error": "order_id, reason, and email are all required"}

    # Find order
    result = await db.execute(
        select(Order).where(Order.order_number == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        return {"error": f"Order {order_id} not found"}

    # Verify email
    customer_result = await db.execute(
        select(Customer).where(Customer.id == order.customer_id)
    )
    customer = customer_result.scalar_one_or_none()

    if customer.email.lower() != email.lower():
        return {"error": "Email does not match this order"}

    # Check if already returned
    if order.return_requested:
        return {"error": "A return has already been requested for this order"}

    # Check return window (30 days)
    if order.status != OrderStatus.DELIVERED:
        return {"error": f"Order status is '{order.status.value}'. Only delivered orders can be returned."}

    if order.delivered_date:
        days_since_delivery = (datetime.utcnow() - order.delivered_date).days
        if days_since_delivery > 30:
            return {
                "error": f"This order was delivered {days_since_delivery} days ago. Our return policy allows returns within 30 days of delivery. However, I can create a support ticket for our team to review your request."
            }

    # Process return
    order.return_requested = True
    order.return_reason = reason
    order.return_approved = True  # Auto-approve for demo
    order.status = OrderStatus.RETURNED
    order.refund_amount = order.total_amount
    order.refund_processed = True

    await db.commit()

    return {
        "success": True,
        "message": f"Return approved for order {order_id}",
        "return_details": {
            "order_number": order_id,
            "refund_amount": order.total_amount,
            "reason": reason,
            "instructions": "A prepaid return shipping label has been sent to your email. Please ship the items within 7 days. Your refund will be processed within 5-7 business days after we receive the return."
        }
    }


async def _get_policy_info(params: dict, db: AsyncSession) -> dict:
    """Get company policy information."""
    policy_type = params.get("policy_type")

    if not policy_type:
        return {"error": "policy_type is required"}

    result = await db.execute(
        select(Policy).where(Policy.policy_type == policy_type)
    )
    policy = result.scalar_one_or_none()

    if not policy:
        return {"error": f"Policy '{policy_type}' not found"}

    return {
        "policy_type": policy.policy_type,
        "title": policy.title,
        "content": policy.content,
        "last_updated": policy.last_updated.strftime("%B %d, %Y"),
    }


async def _get_recommendations(params: dict, db: AsyncSession) -> dict:
    """Get personalized book recommendations."""
    email = params.get("email")
    genre_filter = params.get("genre")
    limit = params.get("limit", 5)

    query = select(Book).where(Book.stock_quantity > 0)

    # Get customer preferences if email provided
    favorite_genres = []
    purchased_ids = []

    if email:
        customer_result = await db.execute(
            select(Customer).where(Customer.email == email)
        )
        customer = customer_result.scalar_one_or_none()

        if customer:
            favorite_genres = customer.favorite_genres or []

            # Get purchased books
            orders_result = await db.execute(
                select(OrderItem.book_id)
                .join(Order)
                .where(Order.customer_id == customer.id)
            )
            purchased_ids = [r[0] for r in orders_result.all()]

    # Exclude purchased books
    if purchased_ids:
        query = query.where(Book.id.notin_(purchased_ids))

    # Filter by genre
    if genre_filter:
        try:
            genre_enum = Genre(genre_filter)
            query = query.where(Book.genre == genre_enum)
        except ValueError:
            pass
    elif favorite_genres:
        genre_enums = []
        for g in favorite_genres:
            try:
                genre_enums.append(Genre(g))
            except ValueError:
                pass
        if genre_enums:
            query = query.where(Book.genre.in_(genre_enums))

    query = query.order_by(Book.rating.desc()).limit(limit)

    result = await db.execute(query)
    books = result.scalars().all()

    return {
        "recommendations": [
            {
                "title": book.title,
                "author": book.author,
                "genre": book.genre.value,
                "price": book.price,
                "rating": book.rating,
                "description": book.description[:200] + "..." if len(book.description) > 200 else book.description,
            }
            for book in books
        ],
        "based_on": f"your preferences ({', '.join(favorite_genres)})" if favorite_genres else "popular books",
    }


async def _search_books(params: dict, db: AsyncSession) -> dict:
    """Search books in catalog."""
    query_text = params.get("query", "")
    genre_filter = params.get("genre")

    if not query_text:
        return {"error": "Search query is required"}

    search_term = f"%{query_text}%"

    query = select(Book).where(
        (Book.title.ilike(search_term)) |
        (Book.author.ilike(search_term))
    )

    if genre_filter:
        try:
            genre_enum = Genre(genre_filter)
            query = query.where(Book.genre == genre_enum)
        except ValueError:
            pass

    query = query.limit(10)

    result = await db.execute(query)
    books = result.scalars().all()

    if not books:
        return {"message": f"No books found matching '{query_text}'", "books": []}

    return {
        "books": [
            {
                "title": book.title,
                "author": book.author,
                "genre": book.genre.value,
                "price": book.price,
                "in_stock": book.stock_quantity > 0,
                "rating": book.rating,
            }
            for book in books
        ],
        "total_found": len(books),
    }


async def _create_support_ticket(params: dict, db: AsyncSession) -> dict:
    """Create a support ticket."""
    email = params.get("email")
    category = params.get("category")
    subject = params.get("subject")
    description = params.get("description")
    priority = params.get("priority", "medium")

    if not all([email, category, subject, description]):
        return {"error": "email, category, subject, and description are required"}

    # Find customer
    customer_result = await db.execute(
        select(Customer).where(Customer.email == email)
    )
    customer = customer_result.scalar_one_or_none()

    if not customer:
        return {"error": f"No account found with email {email}. Please verify your email."}

    # Generate ticket number
    ticket_number = f"TKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    ticket = SupportTicket(
        ticket_number=ticket_number,
        customer_id=customer.id,
        category=category,
        subject=subject,
        description=description,
        priority=TicketPriority(priority),
        status=TicketStatus.OPEN,
    )

    db.add(ticket)
    await db.commit()

    return {
        "success": True,
        "ticket_number": ticket_number,
        "message": f"Support ticket {ticket_number} has been created. Our team will contact you within 24 hours at {email}.",
        "priority": priority,
    }
