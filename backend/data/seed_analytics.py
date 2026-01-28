"""Seed analytics data for dashboard demo.

This script creates realistic analytics data without making actual API calls,
so you can demo the dashboard without using API credits.
"""
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import AsyncSessionLocal
from data.models import Customer, Order, ConversationAnalytics
from analytics.event_collector import (
    track_conversation_start,
    track_conversation_end,
    track_tool_usage,
    track_sentiment,
    track_rating,
    track_event,
)


# Topic categories and their associated tools
TOPIC_TOOLS = {
    "Order Status": ["get_order_status", "search_orders"],
    "Returns & Refunds": ["initiate_return"],
    "Product Information": ["search_books", "get_recommendations"],
    "Policy Questions": ["get_policy_info"],
    "Account Issues": ["get_customer_info"],
    "Escalations": ["create_support_ticket"],
}

# Sentiment messages
POSITIVE_MESSAGES = [
    "Thank you so much for your help!",
    "Great service, really appreciate it!",
    "Perfect, exactly what I needed!",
    "You've been very helpful, thanks!",
    "Excellent support, I'm very satisfied!",
]

NEUTRAL_MESSAGES = [
    "I need to check my order status",
    "What's your return policy?",
    "Can you help me find a book?",
    "I have a question about my account",
    "What books do you recommend?",
]

NEGATIVE_MESSAGES = [
    "I'm frustrated with my order",
    "This is taking too long",
    "I'm disappointed with the service",
    "There's a problem with my order",
    "I need this resolved immediately",
]


async def create_demo_conversation(
    db: AsyncSession,
    user_email: str,
    days_ago: int,
    topic: str,
    sentiment: str,
    resolved: bool,
    escalated: bool,
    csat_score: int = None
):
    """Create a demo conversation with realistic data."""
    session_id = f"demo-{uuid.uuid4().hex[:12]}"
    start_time = datetime.utcnow() - timedelta(days=days_ago)
    
    # Adjust start_time to be more realistic (spread throughout the day)
    hours_offset = random.randint(0, 23)
    minutes_offset = random.randint(0, 59)
    start_time = start_time.replace(hour=hours_offset, minute=minutes_offset)
    
    # Track conversation start
    conv = await track_conversation_start(db, session_id, user_email)
    
    # Update started_at to be more realistic
    conv.started_at = start_time
    await db.commit()
    
    # Simulate messages
    message_count = random.randint(2, 8)
    tools = TOPIC_TOOLS.get(topic, [])
    
    for i in range(message_count):
        # Choose message based on sentiment
        if sentiment == "positive":
            message = random.choice(POSITIVE_MESSAGES)
        elif sentiment == "negative":
            message = random.choice(NEGATIVE_MESSAGES)
        else:
            message = random.choice(NEUTRAL_MESSAGES)
        
        # Track user message
        await track_event(
            db,
            event_type="message_sent",
            session_id=session_id,
            user_email=user_email,
            metadata={
                "message_number": i + 1,
                "content": message[:100],
                "timestamp": (start_time + timedelta(minutes=i*2)).isoformat()
            }
        )
        
        # Track sentiment from first message
        if i == 0:
            await track_sentiment(db, session_id, message)
        
        # Use tools (if available)
        if tools and i < len(tools):
            tool_name = random.choice(tools)
            success = random.random() > 0.15  # 85% success rate
            await track_tool_usage(db, session_id, tool_name, success)
    
    # Calculate end time
    duration_minutes = random.randint(2, 15)
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Update conversation metrics
    conv.message_count = message_count
    conv.tool_count = min(len(tools), message_count)
    
    # Set sentiment score
    sentiment_scores = {"positive": 0.7, "neutral": 0.0, "negative": -0.6}
    conv.sentiment_score = sentiment_scores.get(sentiment, 0.0)
    
    await db.commit()
    
    # Track conversation end (will set resolved/escalated and ended_at)
    await track_conversation_end(db, session_id, resolved=resolved, escalated=escalated)
    
    # Update with our custom timestamps (track_conversation_end uses utcnow())
    conv_result = await db.execute(
        select(ConversationAnalytics).where(ConversationAnalytics.session_id == session_id)
    )
    conv_obj = conv_result.scalar_one()
    conv_obj.ended_at = end_time
    conv_obj.duration_seconds = duration_minutes * 60
    await db.commit()
    
    # Track CSAT rating (70% of resolved conversations get rated)
    if resolved and random.random() < 0.7:
        if csat_score is None:
            # CSAT correlates with sentiment
            if sentiment == "positive":
                csat_score = random.randint(4, 5)
            elif sentiment == "negative":
                csat_score = random.randint(1, 3)
            else:
                csat_score = random.randint(3, 5)
        
        await track_rating(
            db,
            session_id,
            csat_score,
            comment=f"Demo rating for {topic}" if random.random() < 0.2 else None
        )
    
    return session_id


async def seed_analytics_data(
    days_back: int = 30,
    conversations_per_day: int = 10
):
    """Seed analytics data for the past N days."""
    print(f"\n📊 Seeding analytics data...")
    print(f"   Days: {days_back}, Conversations per day: {conversations_per_day}")
    
    async with AsyncSessionLocal() as db:
        # Get existing customers
        result = await db.execute(select(Customer.email))
        customer_emails = [row[0] for row in result.all()]
        
        if not customer_emails:
            print("⚠️  No customers found. Please seed users first.")
            return
        
        # Topic distribution (realistic distribution)
        topic_weights = {
            "Order Status": 0.35,
            "Returns & Refunds": 0.15,
            "Product Information": 0.25,
            "Policy Questions": 0.10,
            "Account Issues": 0.10,
            "Escalations": 0.05,
        }
        
        topics = list(topic_weights.keys())
        topic_probs = list(topic_weights.values())
        
        # Sentiment distribution
        sentiment_weights = {"positive": 0.4, "neutral": 0.45, "negative": 0.15}
        sentiments = list(sentiment_weights.keys())
        sentiment_probs = list(sentiment_weights.values())
        
        total_conversations = 0
        
        # Create conversations for each day
        for day in range(days_back):
            day_date = datetime.utcnow() - timedelta(days=day)
            
            # Vary conversations per day (more on weekdays)
            if day_date.weekday() < 5:  # Weekday
                daily_count = conversations_per_day + random.randint(-2, 3)
            else:  # Weekend
                daily_count = int(conversations_per_day * 0.7) + random.randint(-1, 2)
            
            daily_count = max(1, daily_count)  # At least 1 conversation per day
            
            for _ in range(daily_count):
                # Select topic and sentiment
                topic = random.choices(topics, weights=topic_probs)[0]
                sentiment = random.choices(sentiments, weights=sentiment_probs)[0]
                
                # Determine resolution based on topic and sentiment
                if topic == "Escalations":
                    resolved = False
                    escalated = True
                elif sentiment == "negative" and random.random() < 0.3:
                    resolved = False
                    escalated = True
                else:
                    resolved = random.random() > 0.15  # 85% resolved
                    escalated = not resolved
                
                user_email = random.choice(customer_emails)
                
                try:
                    await create_demo_conversation(
                        db,
                        user_email,
                        days_ago=day,
                        topic=topic,
                        sentiment=sentiment,
                        resolved=resolved,
                        escalated=escalated
                    )
                    total_conversations += 1
                except Exception as e:
                    print(f"  ✗ Failed to create conversation: {e}")
            
            if (day + 1) % 5 == 0:
                print(f"  ✓ Created conversations for {day + 1} days ({total_conversations} total)")
        
        print(f"\n✅ Seeded {total_conversations} conversations across {days_back} days")
        print(f"   Data is ready for dashboard demo!")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed analytics data for dashboard demo")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to generate data for (default: 30)"
    )
    parser.add_argument(
        "--per-day",
        type=int,
        default=10,
        help="Average conversations per day (default: 10)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Analytics Data Seeding")
    print("=" * 60)
    print("This script creates demo analytics data WITHOUT making API calls")
    print("Perfect for dashboard demos without using API credits!")
    print("=" * 60)
    
    await seed_analytics_data(
        days_back=args.days,
        conversations_per_day=args.per_day
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
