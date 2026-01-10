"""Generate ~45 orders with mixed statuses and edge cases."""
import random
from datetime import datetime, timedelta
from .models import Order, OrderItem, OrderStatus, SupportTicket, TicketStatus, TicketPriority, Policy


def generate_order_number(index: int) -> str:
    """Generate a realistic order number."""
    year = datetime.utcnow().year
    return f"ORD-{year}-{str(index).zfill(5)}"


def generate_tracking_number() -> str:
    """Generate a realistic tracking number."""
    carriers = {
        "USPS": "9400111899",
        "FedEx": "7489",
        "UPS": "1Z999AA1"
    }
    carrier = random.choice(list(carriers.keys()))
    prefix = carriers[carrier]
    suffix = "".join([str(random.randint(0, 9)) for _ in range(12 - len(prefix))])
    return f"{prefix}{suffix}", carrier


# Order configurations for each user
# Format: (customer_email, orders_config)
# Each order_config: (status, days_ago, return_status, special_notes)
ORDER_CONFIGS = {
    "sarah.johnson@email.com": [
        # 5 orders - primary demo user with mixed statuses
        (OrderStatus.DELIVERED, 60, None, "Old delivered order"),
        (OrderStatus.DELIVERED, 30, None, "Recent delivered order"),
        (OrderStatus.SHIPPED, 3, None, "Currently shipping - main demo"),
        (OrderStatus.PROCESSING, 1, None, "Just placed"),
        (OrderStatus.PENDING, 0, None, "Newest order"),
    ],
    "mike.chen@email.com": [
        # 3 orders - tech reader
        (OrderStatus.DELIVERED, 90, None, "Old order"),
        (OrderStatus.DELIVERED, 45, None, "Recent order"),
        (OrderStatus.SHIPPED, 5, None, "In transit"),
    ],
    "emma.wilson@email.com": [
        # 8 orders - heavy buyer with some old orders (outside return window)
        (OrderStatus.DELIVERED, 180, None, "Very old - outside return window"),
        (OrderStatus.DELIVERED, 120, None, "Old - outside return window"),
        (OrderStatus.DELIVERED, 90, None, "Old order"),
        (OrderStatus.DELIVERED, 60, None, "Within return window"),
        (OrderStatus.DELIVERED, 45, None, "Within return window"),
        (OrderStatus.DELIVERED, 30, None, "Recent"),
        (OrderStatus.SHIPPED, 4, None, "Shipping"),
        (OrderStatus.PROCESSING, 1, None, "Processing"),
    ],
    "james.garcia@email.com": [
        # 1 order - new customer
        (OrderStatus.PENDING, 0, None, "First order, pending"),
    ],
    "olivia.smith@email.com": [
        # 4 orders - 2 already returned (test return eligibility)
        (OrderStatus.RETURNED, 45, "returned", "Already returned"),
        (OrderStatus.RETURNED, 30, "returned", "Already returned"),
        (OrderStatus.DELIVERED, 15, None, "Can be returned"),
        (OrderStatus.SHIPPED, 2, None, "In transit"),
    ],
    "david.kim@email.com": [
        # 0 orders - browser only
    ],
    "sophia.martinez@email.com": [
        # 12 orders - power user
        (OrderStatus.DELIVERED, 300, None, "Very old"),
        (OrderStatus.DELIVERED, 250, None, "Old"),
        (OrderStatus.DELIVERED, 200, None, "Old"),
        (OrderStatus.DELIVERED, 150, None, "Old"),
        (OrderStatus.DELIVERED, 100, None, "Medium age"),
        (OrderStatus.DELIVERED, 75, None, "Medium age"),
        (OrderStatus.DELIVERED, 50, None, "Within return window"),
        (OrderStatus.DELIVERED, 30, None, "Recent"),
        (OrderStatus.DELIVERED, 15, None, "Recent"),
        (OrderStatus.SHIPPED, 5, None, "Shipping"),
        (OrderStatus.PROCESSING, 2, None, "Processing"),
        (OrderStatus.PENDING, 0, None, "Newest"),
    ],
    "alex.taylor@email.com": [
        # 2 orders - no preferences set
        (OrderStatus.DELIVERED, 25, None, "Delivered"),
        (OrderStatus.SHIPPED, 3, None, "Shipping"),
    ],
    "rachel.brown@email.com": [
        # 3 orders - 1 with dispute/support ticket
        (OrderStatus.DELIVERED, 60, None, "Old order"),
        (OrderStatus.DELIVERED, 20, "disputed", "Has support ticket"),
        (OrderStatus.SHIPPED, 4, None, "In transit"),
    ],
    "chris.lee@email.com": [
        # 6 orders - standard user
        (OrderStatus.DELIVERED, 120, None, "Old"),
        (OrderStatus.DELIVERED, 90, None, "Old"),
        (OrderStatus.DELIVERED, 60, None, "Medium"),
        (OrderStatus.DELIVERED, 30, None, "Recent"),
        (OrderStatus.SHIPPED, 5, None, "Shipping"),
        (OrderStatus.CANCELLED, 10, "cancelled", "Cancelled order"),
    ],
}


async def seed_orders(session):
    """Seed the database with orders."""
    from sqlalchemy import select
    from .models import Customer, Book

    # Check if orders already exist
    result = await session.execute(select(Order).limit(1))
    if result.scalar_one_or_none():
        print("Orders already seeded, skipping...")
        return

    # Get all customers
    result = await session.execute(select(Customer))
    customers = {c.email: c for c in result.scalars().all()}

    # Get all books for random selection
    result = await session.execute(select(Book))
    books = list(result.scalars().all())

    if not books:
        print("No books found. Please seed books first.")
        return

    print("Creating ~45 orders with edge cases...")
    order_index = 1

    for email, order_configs in ORDER_CONFIGS.items():
        customer = customers.get(email)
        if not customer:
            print(f"Customer {email} not found, skipping orders...")
            continue

        for status, days_ago, special_status, notes in order_configs:
            order_date = datetime.utcnow() - timedelta(days=days_ago)

            # Generate order number
            order_number = generate_order_number(order_index)
            order_index += 1

            # Random 1-4 items per order
            num_items = random.randint(1, 4)
            selected_books = random.sample(books, min(num_items, len(books)))

            # Calculate total
            total_amount = 0
            order_items_data = []
            for book in selected_books:
                quantity = random.randint(1, 2)
                total_amount += book.price * quantity
                order_items_data.append({
                    "book": book,
                    "quantity": quantity,
                    "price_per_unit": book.price
                })

            # Add shipping cost for non-free shipping orders
            if total_amount < 35:
                shipping_cost = 4.99
                total_amount += shipping_cost

            total_amount = round(total_amount, 2)

            # Shipping info
            tracking_number = None
            carrier = None
            shipped_date = None
            delivered_date = None
            estimated_delivery = None

            if status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                tracking_number, carrier = generate_tracking_number()
                shipped_date = order_date + timedelta(days=1)

                if status == OrderStatus.DELIVERED:
                    delivered_date = shipped_date + timedelta(days=random.randint(3, 7))
                else:
                    estimated_delivery = shipped_date + timedelta(days=random.randint(3, 7))

            # Return info
            return_requested = special_status == "returned"
            return_approved = return_requested
            refund_processed = return_requested
            refund_amount = total_amount if return_requested else 0

            # Create order
            order = Order(
                order_number=order_number,
                customer_id=customer.id,
                status=status,
                total_amount=total_amount,
                shipping_address=customer.shipping_address,
                shipping_method="standard" if total_amount < 50 else "express",
                tracking_number=tracking_number,
                carrier=carrier,
                estimated_delivery=estimated_delivery,
                return_requested=return_requested,
                return_approved=return_approved,
                refund_amount=refund_amount,
                refund_processed=refund_processed,
                order_date=order_date,
                shipped_date=shipped_date,
                delivered_date=delivered_date,
            )

            session.add(order)
            await session.flush()  # Get the order ID

            # Add order items
            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=item_data["book"].id,
                    quantity=item_data["quantity"],
                    price_per_unit=item_data["price_per_unit"]
                )
                session.add(order_item)

            # Create support ticket for disputed order
            if special_status == "disputed":
                ticket = SupportTicket(
                    ticket_number=f"TKT-{order_number}",
                    customer_id=customer.id,
                    category="order",
                    subject=f"Issue with order {order_number}",
                    description="I received a damaged book in my order. The cover is torn and some pages are bent.",
                    priority=TicketPriority.HIGH,
                    status=TicketStatus.IN_PROGRESS,
                    created_at=order_date + timedelta(days=5),
                )
                session.add(ticket)

    await session.commit()
    print(f"Seeded {order_index - 1} orders successfully!")


async def seed_policies(session):
    """Seed company policies for agent grounding."""
    from sqlalchemy import select

    # Check if policies already exist
    result = await session.execute(select(Policy).limit(1))
    if result.scalar_one_or_none():
        print("Policies already seeded, skipping...")
        return

    policies = [
        {
            "policy_type": "return",
            "title": "Return Policy",
            "content": """Bookly Return Policy

ELIGIBILITY:
- Returns accepted within 30 days of delivery date
- Books must be in original condition (unopened for sealed items)
- Digital books and ebooks are non-returnable
- Textbooks with access codes are non-returnable if code has been used

PROCESS:
1. Contact customer support to initiate a return
2. Receive a prepaid return shipping label via email
3. Pack the book securely and ship within 7 days
4. Refund processed within 5-7 business days after receipt

SHIPPING COSTS:
- Free return shipping for defective or incorrect items
- Customer pays $4.99 return shipping for change-of-mind returns
- Original shipping costs are non-refundable

EXCEPTIONS:
- Items damaged during shipping: Full refund including shipping
- Wrong item received: Full refund plus free expedited shipping for correct item
- Defective products: Full refund or replacement at customer's choice

For questions, contact support@bookly.com or call 1-800-BOOKLY."""
        },
        {
            "policy_type": "shipping",
            "title": "Shipping Policy",
            "content": """Bookly Shipping Policy

SHIPPING METHODS & TIMES:
- Standard Shipping (5-7 business days): $4.99
- Express Shipping (2-3 business days): $9.99
- Overnight Shipping (1 business day): $19.99

FREE SHIPPING:
- Standard shipping is FREE on orders over $35
- Free shipping applies to US addresses only

PROCESSING TIME:
- Orders placed before 2 PM EST ship same business day
- Orders placed after 2 PM EST ship next business day
- Processing may take 1-2 additional days during peak seasons

TRACKING:
- Tracking number provided via email once shipped
- Track your order at bookly.com/track or carrier website

SHIPPING DESTINATIONS:
- We ship to all 50 US states
- International shipping available (additional fees apply)
- PO Boxes accepted for Standard shipping only

DELIVERY ISSUES:
- Package not received: Contact us within 14 days of expected delivery
- Damaged in transit: Take photos and contact us within 48 hours
- Wrong address: Customer responsible for orders shipped to incorrect address provided"""
        },
        {
            "policy_type": "refund",
            "title": "Refund Policy",
            "content": """Bookly Refund Policy

REFUND TIMELINE:
- Refunds processed within 5-7 business days after return received
- Credit card refunds may take 1-2 billing cycles to appear
- Store credit issued within 24 hours of return approval

REFUND METHODS:
- Original payment method (credit card, debit card)
- Store credit (if preferred, includes 10% bonus)
- PayPal refunds processed within 3-5 business days

REFUND AMOUNTS:
- Full refund: Item cost minus any applicable return shipping
- Partial refund: May apply if item is damaged or not in original condition
- Shipping costs: Non-refundable except for our errors

SPECIAL CASES:
- Pre-orders cancelled before shipping: Full refund within 3 business days
- Bundle purchases: Refund calculated based on individual item prices
- Sale items: Refund based on price paid, not original price

STORE CREDIT:
- Never expires
- Can be combined with other promotions
- Transferable with customer service approval

For expedited refund processing, contact customer support."""
        },
        {
            "policy_type": "privacy",
            "title": "Privacy Policy",
            "content": """Bookly Privacy Policy (Summary)

INFORMATION WE COLLECT:
- Account information (name, email, shipping address)
- Order history and preferences
- Payment information (processed securely, not stored)
- Browsing behavior on our site

HOW WE USE YOUR DATA:
- Process orders and provide customer service
- Send order updates and shipping notifications
- Personalize book recommendations
- Send marketing emails (with your consent)

DATA PROTECTION:
- SSL encryption for all transactions
- No selling of personal data to third parties
- Regular security audits
- Compliant with CCPA and GDPR

YOUR RIGHTS:
- Access your personal data
- Request data deletion
- Opt out of marketing communications
- Download your order history

For full privacy policy, visit bookly.com/privacy
Contact: privacy@bookly.com"""
        },
        {
            "policy_type": "payment",
            "title": "Payment Policy",
            "content": """Bookly Payment Policy

ACCEPTED PAYMENT METHODS:
- Credit Cards: Visa, MasterCard, American Express, Discover
- Debit Cards: With Visa/MasterCard logo
- PayPal
- Apple Pay / Google Pay
- Bookly Gift Cards
- Store Credit

PAYMENT SECURITY:
- All transactions encrypted with 256-bit SSL
- PCI DSS compliant
- No credit card information stored on our servers

BILLING:
- Payment charged when order ships
- Pre-orders charged when item becomes available
- Subscription boxes charged on billing date

PAYMENT ISSUES:
- Declined card: We'll email you to update payment
- Fraudulent charges: Report within 60 days for investigation
- Price match: Contact us within 14 days of purchase

GIFT CARDS:
- No expiration date
- Cannot be redeemed for cash
- Lost cards can be replaced with proof of purchase"""
        },
        {
            "policy_type": "account",
            "title": "Account Policy",
            "content": """Bookly Account Policy

ACCOUNT CREATION:
- Free to create and maintain
- One account per email address
- Must be 18+ or have parental consent

ACCOUNT FEATURES:
- Save shipping addresses
- View order history
- Track shipments
- Manage preferences
- Faster checkout

PASSWORD REQUIREMENTS:
- Minimum 8 characters
- At least one number
- At least one uppercase letter
- Password reset via email only

ACCOUNT SECURITY:
- We never ask for password via email or phone
- Enable two-factor authentication for added security
- Review login history in account settings
- Report suspicious activity immediately

ACCOUNT DELETION:
- Request via account settings or customer support
- Order history retained for 7 years (legal requirement)
- Personal data deleted within 30 days
- Any store credit forfeited upon deletion

For account assistance: support@bookly.com"""
        },
    ]

    for policy_data in policies:
        policy = Policy(**policy_data)
        session.add(policy)

    await session.commit()
    print(f"Seeded {len(policies)} policies successfully!")
