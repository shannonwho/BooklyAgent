"""Generate 10 user profiles with varied preferences for edge case testing."""
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from .models import Customer, Genre

# Password for all demo accounts
DEMO_PASSWORD = "demo123"


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hash(password)


# 10 User profiles with different characteristics for testing
USER_PROFILES = [
    {
        "email": "sarah.johnson@email.com",
        "name": "Sarah Johnson",
        "phone": "+1-555-0101",
        "favorite_genres": [Genre.FICTION.value, Genre.MYSTERY.value],
        "shipping_address": {
            "name": "Sarah Johnson",
            "street": "123 Main Street",
            "city": "Boston",
            "state": "MA",
            "zip": "02101",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=365),
        "description": "Primary demo - multiple orders, active shopper"
    },
    {
        "email": "mike.chen@email.com",
        "name": "Mike Chen",
        "phone": "+1-555-0102",
        "favorite_genres": [Genre.SCIFI.value, Genre.BUSINESS.value],
        "shipping_address": {
            "name": "Mike Chen",
            "street": "456 Tech Drive",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=180),
        "description": "Tech-focused reader"
    },
    {
        "email": "emma.wilson@email.com",
        "name": "Emma Wilson",
        "phone": "+1-555-0103",
        "favorite_genres": [Genre.ROMANCE.value, Genre.SELF_HELP.value],
        "shipping_address": {
            "name": "Emma Wilson",
            "street": "789 Garden Lane",
            "city": "Seattle",
            "state": "WA",
            "zip": "98101",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=730),  # 2 years
        "description": "Heavy buyer - lots of history for recommendations"
    },
    {
        "email": "james.garcia@email.com",
        "name": "James Garcia",
        "phone": "+1-555-0104",
        "favorite_genres": [Genre.HISTORY.value, Genre.BIOGRAPHY.value],
        "shipping_address": {
            "name": "James Garcia",
            "street": "321 Oak Avenue",
            "city": "Austin",
            "state": "TX",
            "zip": "78701",
            "country": "USA"
        },
        "newsletter_subscribed": False,
        "created_at": datetime.utcnow() - timedelta(days=14),  # 2 weeks ago
        "description": "New customer - minimal history"
    },
    {
        "email": "olivia.smith@email.com",
        "name": "Olivia Smith",
        "phone": "+1-555-0105",
        "favorite_genres": [Genre.FANTASY.value, Genre.SCIFI.value],
        "shipping_address": {
            "name": "Olivia Smith",
            "street": "555 Fantasy Road",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=200),
        "description": "Return history - test return eligibility"
    },
    {
        "email": "david.kim@email.com",
        "name": "David Kim",
        "phone": "+1-555-0106",
        "favorite_genres": [Genre.THRILLER.value, Genre.MYSTERY.value],
        "shipping_address": {
            "name": "David Kim",
            "street": "777 Suspense Street",
            "city": "Chicago",
            "state": "IL",
            "zip": "60601",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=90),
        "description": "Browser only - no purchase history"
    },
    {
        "email": "sophia.martinez@email.com",
        "name": "Sophia Martinez",
        "phone": "+1-555-0107",
        "favorite_genres": [
            Genre.FICTION.value, Genre.ROMANCE.value, Genre.MYSTERY.value,
            Genre.SELF_HELP.value, Genre.FANTASY.value
        ],
        "shipping_address": {
            "name": "Sophia Martinez",
            "street": "888 Reader's Paradise",
            "city": "Miami",
            "state": "FL",
            "zip": "33101",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=500),
        "description": "Power user - diverse taste, many orders"
    },
    {
        "email": "alex.taylor@email.com",
        "name": "Alex Taylor",
        "phone": "+1-555-0108",
        "favorite_genres": [],  # No preferences set
        "shipping_address": {
            "name": "Alex Taylor",
            "street": "999 New User Lane",
            "city": "Denver",
            "state": "CO",
            "zip": "80201",
            "country": "USA"
        },
        "newsletter_subscribed": False,
        "created_at": datetime.utcnow() - timedelta(days=30),
        "description": "No preferences - test cold-start recommendations"
    },
    {
        "email": "rachel.brown@email.com",
        "name": "Rachel Brown",
        "phone": "+1-555-0109",
        "favorite_genres": [Genre.SELF_HELP.value, Genre.BUSINESS.value],
        "shipping_address": {
            "name": "Rachel Brown",
            "street": "111 Support Street",
            "city": "Atlanta",
            "state": "GA",
            "zip": "30301",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=150),
        "description": "Support case - has open support ticket"
    },
    {
        "email": "chris.lee@email.com",
        "name": "Chris Lee",
        "phone": "+1-555-0110",
        "favorite_genres": [Genre.FICTION.value, Genre.FANTASY.value],
        "shipping_address": {
            "name": "Chris Lee",
            "street": "222 Standard Avenue",
            "city": "Philadelphia",
            "state": "PA",
            "zip": "19101",
            "country": "USA"
        },
        "newsletter_subscribed": True,
        "created_at": datetime.utcnow() - timedelta(days=300),
        "description": "Standard user"
    },
]


async def seed_users(session, force: bool = False):
    """Seed the database with user profiles.
    
    Args:
        session: Database session
        force: If True, reseed even if users already exist
    """
    from sqlalchemy import select
    import os

    # Check if we should force reseed (from environment variable)
    force_reseed = force or os.getenv("FORCE_RESeed", "").lower() in ("true", "1", "yes")

    # Check if users already exist
    if not force_reseed:
        try:
            from sqlalchemy import func
            result = await session.execute(select(func.count(Customer.id)))
            user_count = result.scalar() or 0
            if user_count > 0:
                print(f"Found {user_count} existing users, skipping seed...")
                print("To force reseed, set FORCE_RESeed=true or use force=True")
                return
            else:
                print(f"No users found in database (count: {user_count}), proceeding with seed...")
        except Exception as e:
            print(f"Error checking for existing users: {e}")
            print("Proceeding with seed anyway...")
            # Continue with seeding if check fails

    if force_reseed:
        print("Force reseeding enabled - clearing existing users...")
        from sqlalchemy import delete
        await session.execute(delete(Customer))
        await session.commit()

    print("Creating 10 user profiles...")
    try:
        password_hash = get_password_hash(DEMO_PASSWORD)

        for profile in USER_PROFILES:
            # Remove description (not a model field)
            profile_data = {k: v for k, v in profile.items() if k != "description"}
            profile_data["password_hash"] = password_hash

            customer = Customer(**profile_data)
            session.add(customer)

        await session.commit()
        print("Seeded 10 user profiles successfully!")
    except Exception as e:
        await session.rollback()
        print(f"Error seeding users: {e}")
        import traceback
        traceback.print_exc()
        raise


def get_user_profiles_info():
    """Return user profile info for documentation."""
    return [
        {
            "email": p["email"],
            "name": p["name"],
            "preferences": p["favorite_genres"],
            "description": p["description"]
        }
        for p in USER_PROFILES
    ]
