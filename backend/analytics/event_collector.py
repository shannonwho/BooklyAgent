"""Event collector for analytics tracking."""
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from data.models import AnalyticsEvent, ConversationAnalytics, TopicAnalytics


# Topic categorization mapping
TOOL_TO_TOPIC = {
    "get_order_status": "Order Status",
    "search_orders": "Order Status",
    "initiate_return": "Returns & Refunds",
    "search_books": "Product Information",
    "get_recommendations": "Product Information",
    "get_policy_info": "Policy Questions",
    "get_customer_info": "Account Issues",
    "create_support_ticket": "Escalations",
}

# Sentiment keywords
POSITIVE_KEYWORDS = ["thank", "thanks", "great", "helpful", "excellent", "perfect", "good", "appreciate", "awesome"]
NEGATIVE_KEYWORDS = ["frustrated", "disappointed", "problem", "issue", "wrong", "bad", "terrible", "horrible", "angry", "upset"]


def get_topic_category(tool_name: str) -> str:
    """Map tool name to topic category."""
    return TOOL_TO_TOPIC.get(tool_name, "Other")


def analyze_sentiment(text: str) -> Optional[str]:
    """Simple keyword-based sentiment analysis."""
    if not text:
        return None
    
    text_lower = text.lower()
    positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text_lower)
    negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text_lower)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"


async def track_event(
    db: AsyncSession,
    event_type: str,
    session_id: Optional[str] = None,
    user_email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AnalyticsEvent:
    """Track a generic analytics event."""
    event = AnalyticsEvent(
        event_type=event_type,
        session_id=session_id,
        user_email=user_email,
        timestamp=datetime.utcnow(),
        event_metadata=metadata or {}
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def track_conversation_start(
    db: AsyncSession,
    session_id: str,
    user_email: Optional[str] = None
) -> ConversationAnalytics:
    """Track the start of a conversation."""
    # Check if conversation already exists
    result = await db.execute(
        select(ConversationAnalytics).where(ConversationAnalytics.session_id == session_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return existing
    
    conversation = ConversationAnalytics(
        session_id=session_id,
        user_email=user_email,
        started_at=datetime.utcnow(),
        message_count=0,
        tool_count=0,
        tools_used=[],
        resolved=False,
        escalated=False
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    # Also track as event
    await track_event(
        db,
        event_type="chat_started",
        session_id=session_id,
        user_email=user_email,
        metadata={"conversation_id": conversation.id}
    )
    
    return conversation


async def track_conversation_end(
    db: AsyncSession,
    session_id: str,
    resolved: bool = False,
    escalated: bool = False
) -> Optional[ConversationAnalytics]:
    """Track the end of a conversation."""
    result = await db.execute(
        select(ConversationAnalytics).where(ConversationAnalytics.session_id == session_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        return None
    
    conversation.ended_at = datetime.utcnow()
    conversation.resolved = resolved
    conversation.escalated = escalated
    
    if conversation.started_at and conversation.ended_at:
        duration = (conversation.ended_at - conversation.started_at).total_seconds()
        conversation.duration_seconds = duration
    
    await db.commit()
    await db.refresh(conversation)
    
    # Track as event
    await track_event(
        db,
        event_type="conversation_ended",
        session_id=session_id,
        user_email=conversation.user_email,
        metadata={
            "resolved": resolved,
            "escalated": escalated,
            "duration_seconds": conversation.duration_seconds,
            "message_count": conversation.message_count,
            "tool_count": conversation.tool_count
        }
    )
    
    return conversation


async def track_tool_usage(
    db: AsyncSession,
    session_id: str,
    tool_name: str,
    success: bool = True
) -> None:
    """Track tool usage in a conversation."""
    result = await db.execute(
        select(ConversationAnalytics).where(ConversationAnalytics.session_id == session_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        conversation.tool_count += 1
        if conversation.tools_used is None:
            conversation.tools_used = []
        if tool_name not in conversation.tools_used:
            conversation.tools_used.append(tool_name)
        await db.commit()
    
    # Track topic
    topic_category = get_topic_category(tool_name)
    
    # Get or create topic analytics for today
    today = datetime.utcnow().date()
    topic_result = await db.execute(
        select(TopicAnalytics).where(
            TopicAnalytics.topic_category == topic_category,
            TopicAnalytics.date >= datetime.combine(today, datetime.min.time()),
            TopicAnalytics.date < datetime.combine(today, datetime.max.time())
        )
    )
    topic_analytics = topic_result.scalar_one_or_none()
    
    if not topic_analytics:
        topic_analytics = TopicAnalytics(
            topic_category=topic_category,
            date=datetime.utcnow(),
            count=0,
            success_rate=0.0,
            escalation_rate=0.0
        )
        db.add(topic_analytics)
    
    topic_analytics.count += 1
    
    # Update success rate (simplified - would need more data for accurate calculation)
    if success:
        if topic_analytics.success_rate is None:
            topic_analytics.success_rate = 100.0
        else:
            # Simple moving average
            topic_analytics.success_rate = (topic_analytics.success_rate * (topic_analytics.count - 1) + 100.0) / topic_analytics.count
    else:
        if topic_analytics.success_rate is None:
            topic_analytics.success_rate = 0.0
        else:
            topic_analytics.success_rate = (topic_analytics.success_rate * (topic_analytics.count - 1) + 0.0) / topic_analytics.count
    
    await db.commit()
    
    # Track as event
    await track_event(
        db,
        event_type="tool_used",
        session_id=session_id,
        metadata={
            "tool_name": tool_name,
            "topic_category": topic_category,
            "success": success
        }
    )


async def track_sentiment(
    db: AsyncSession,
    session_id: str,
    text: str
) -> None:
    """Track sentiment in a conversation."""
    sentiment = analyze_sentiment(text)
    
    if not sentiment:
        return
    
    result = await db.execute(
        select(ConversationAnalytics).where(ConversationAnalytics.session_id == session_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        # Simple sentiment scoring: positive = 1, neutral = 0, negative = -1
        sentiment_value = 1.0 if sentiment == "positive" else (-1.0 if sentiment == "negative" else 0.0)
        
        if conversation.sentiment_score is None:
            conversation.sentiment_score = sentiment_value
        else:
            # Weighted average (favor recent sentiment)
            conversation.sentiment_score = (conversation.sentiment_score * 0.7 + sentiment_value * 0.3)
        
        await db.commit()
    
    await track_event(
        db,
        event_type="sentiment_detected",
        session_id=session_id,
        metadata={"sentiment": sentiment, "text_preview": text[:100]}
    )


async def track_rating(
    db: AsyncSession,
    session_id: str,
    rating: int,
    comment: Optional[str] = None
) -> None:
    """Track CSAT rating for a conversation."""
    if rating < 1 or rating > 5:
        return
    
    result = await db.execute(
        select(ConversationAnalytics).where(ConversationAnalytics.session_id == session_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        conversation.csat_score = rating
        await db.commit()
    
    await track_event(
        db,
        event_type="rating_submitted",
        session_id=session_id,
        user_email=conversation.user_email if conversation else None,
        metadata={
            "rating": rating,
            "comment": comment
        }
    )
