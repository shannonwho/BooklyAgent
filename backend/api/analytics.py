"""Analytics API endpoints."""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from data.database import get_db
from data.models import (
    AnalyticsEvent,
    ConversationAnalytics,
    TopicAnalytics,
    SupportTicket
)

router = APIRouter()


def parse_time_range(time_range: str) -> tuple[datetime, datetime]:
    """Parse time range string to start and end datetimes."""
    now = datetime.utcnow()
    
    if time_range == "24h":
        start = now - timedelta(hours=24)
    elif time_range == "7d":
        start = now - timedelta(days=7)
    elif time_range == "30d":
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(days=7)  # Default to 7 days
    
    return start, now


@router.get("/dashboard")
async def get_dashboard_metrics(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get overall dashboard metrics."""
    start_date, end_date = parse_time_range(time_range)
    
    # Total conversations
    conversations_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date
        )
    )
    total_conversations = conversations_result.scalar() or 0
    
    # Average CSAT score
    csat_result = await db.execute(
        select(func.avg(ConversationAnalytics.csat_score)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.csat_score.isnot(None)
        )
    )
    avg_csat = csat_result.scalar()
    avg_csat = round(avg_csat, 2) if avg_csat else None
    
    # Resolution rate
    resolved_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.resolved == True
        )
    )
    resolved_count = resolved_result.scalar() or 0
    resolution_rate = (resolved_count / total_conversations * 100) if total_conversations > 0 else 0
    
    # Top 5 topics
    topics_result = await db.execute(
        select(
            TopicAnalytics.topic_category,
            func.sum(TopicAnalytics.count).label("total_count")
        ).where(
            TopicAnalytics.date >= start_date,
            TopicAnalytics.date <= end_date
        ).group_by(TopicAnalytics.topic_category).order_by(func.sum(TopicAnalytics.count).desc()).limit(5)
    )
    top_topics = [
        {"topic": row[0], "count": row[1]}
        for row in topics_result.all()
    ]
    
    # Conversation volume trend (last 7 days)
    trend_start = end_date - timedelta(days=7)
    trend_result = await db.execute(
        select(
            func.date(ConversationAnalytics.started_at).label("date"),
            func.count(ConversationAnalytics.id).label("count")
        ).where(
            ConversationAnalytics.started_at >= trend_start,
            ConversationAnalytics.started_at <= end_date
        ).group_by(func.date(ConversationAnalytics.started_at)).order_by(func.date(ConversationAnalytics.started_at))
    )
    volume_trend = [
        {"date": row[0].isoformat(), "count": row[1]}
        for row in trend_result.all()
    ]
    
    return {
        "total_conversations": total_conversations,
        "avg_csat_score": avg_csat,
        "resolution_rate": round(resolution_rate, 2),
        "top_topics": top_topics,
        "volume_trend": volume_trend,
        "time_range": time_range
    }


@router.get("/satisfaction")
async def get_satisfaction_metrics(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get CSAT and satisfaction metrics."""
    start_date, end_date = parse_time_range(time_range)
    
    # CSAT score over time
    csat_trend_result = await db.execute(
        select(
            func.date(ConversationAnalytics.started_at).label("date"),
            func.avg(ConversationAnalytics.csat_score).label("avg_csat")
        ).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.csat_score.isnot(None)
        ).group_by(func.date(ConversationAnalytics.started_at)).order_by(func.date(ConversationAnalytics.started_at))
    )
    csat_trend = [
        {"date": row[0].isoformat(), "avg_csat": round(row[1], 2)}
        for row in csat_trend_result.all()
    ]
    
    # Sentiment distribution
    sentiment_result = await db.execute(
        select(
            func.count(ConversationAnalytics.id).label("count"),
            func.avg(ConversationAnalytics.sentiment_score).label("avg_sentiment")
        ).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.sentiment_score.isnot(None)
        )
    )
    sentiment_data = sentiment_result.first()
    
    # Response time metrics
    response_time_result = await db.execute(
        select(
            func.avg(ConversationAnalytics.duration_seconds).label("avg_duration"),
            func.min(ConversationAnalytics.duration_seconds).label("min_duration"),
            func.max(ConversationAnalytics.duration_seconds).label("max_duration")
        ).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.duration_seconds.isnot(None)
        )
    )
    response_time_data = response_time_result.first()
    
    # Resolution rate breakdown
    total_conversations_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date
        )
    )
    total_conversations = total_conversations_result.scalar() or 0
    
    resolved_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.resolved == True
        )
    )
    resolved_count = resolved_result.scalar() or 0
    
    escalated_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.escalated == True
        )
    )
    escalated_count = escalated_result.scalar() or 0
    
    return {
        "csat_trend": csat_trend,
        "sentiment": {
            "total_with_sentiment": sentiment_data[0] if sentiment_data else 0,
            "avg_sentiment_score": round(sentiment_data[1], 2) if sentiment_data and sentiment_data[1] else None
        },
        "response_times": {
            "avg_seconds": round(response_time_data[0], 2) if response_time_data and response_time_data[0] else None,
            "min_seconds": round(response_time_data[1], 2) if response_time_data and response_time_data[1] else None,
            "max_seconds": round(response_time_data[2], 2) if response_time_data and response_time_data[2] else None
        },
        "resolution_breakdown": {
            "total": total_conversations,
            "resolved": resolved_count,
            "escalated": escalated_count,
            "resolution_rate": round((resolved_count / total_conversations * 100), 2) if total_conversations > 0 else 0,
            "escalation_rate": round((escalated_count / total_conversations * 100), 2) if total_conversations > 0 else 0
        }
    }


@router.get("/topics")
async def get_topic_analytics(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get topic distribution and trends."""
    start_date, end_date = parse_time_range(time_range)
    
    # Topic frequency distribution
    topic_freq_result = await db.execute(
        select(
            TopicAnalytics.topic_category,
            func.sum(TopicAnalytics.count).label("total_count"),
            func.avg(TopicAnalytics.success_rate).label("avg_success_rate"),
            func.avg(TopicAnalytics.escalation_rate).label("avg_escalation_rate")
        ).where(
            TopicAnalytics.date >= start_date,
            TopicAnalytics.date <= end_date
        ).group_by(TopicAnalytics.topic_category).order_by(func.sum(TopicAnalytics.count).desc())
    )
    topic_distribution = [
        {
            "topic": row[0],
            "count": row[1],
            "success_rate": round(row[2], 2) if row[2] else None,
            "escalation_rate": round(row[3], 2) if row[3] else None
        }
        for row in topic_freq_result.all()
    ]
    
    # Topic trends over time
    topic_trends_result = await db.execute(
        select(
            func.date(TopicAnalytics.date).label("date"),
            TopicAnalytics.topic_category,
            func.sum(TopicAnalytics.count).label("count")
        ).where(
            TopicAnalytics.date >= start_date,
            TopicAnalytics.date <= end_date
        ).group_by(func.date(TopicAnalytics.date), TopicAnalytics.topic_category).order_by(func.date(TopicAnalytics.date))
    )
    
    # Group by date
    trends_by_date = {}
    for row in topic_trends_result.all():
        date_str = row[0].isoformat()
        if date_str not in trends_by_date:
            trends_by_date[date_str] = {}
        trends_by_date[date_str][row[1]] = row[2]
    
    # Convert to list format
    topic_trends = [
        {"date": date, **topics}
        for date, topics in trends_by_date.items()
    ]
    
    return {
        "distribution": topic_distribution,
        "trends": topic_trends,
        "time_range": time_range
    }


@router.get("/conversations")
async def get_conversation_analytics(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    topic: Optional[str] = None,
    user_email: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation analytics list."""
    query = select(ConversationAnalytics)
    
    if topic:
        # Filter by topic (check if topic appears in tools_used)
        # This is a simplified approach - in production, you'd want a better way to filter
        query = query.where(ConversationAnalytics.tools_used.contains([topic]))
    
    if user_email:
        query = query.where(ConversationAnalytics.user_email == user_email)
    
    query = query.order_by(ConversationAnalytics.started_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return {
        "conversations": [
            {
                "session_id": conv.session_id,
                "user_email": conv.user_email,
                "started_at": conv.started_at.isoformat(),
                "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
                "message_count": conv.message_count,
                "tool_count": conv.tool_count,
                "tools_used": conv.tools_used,
                "sentiment_score": conv.sentiment_score,
                "csat_score": conv.csat_score,
                "resolved": conv.resolved,
                "escalated": conv.escalated,
                "duration_seconds": conv.duration_seconds
            }
            for conv in conversations
        ],
        "limit": limit,
        "offset": offset
    }


@router.get("/trends")
async def get_trends(
    metric: str = Query("conversations", description="Metric: conversations, csat, topics"),
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get time-series trends."""
    start_date, end_date = parse_time_range(time_range)
    
    if metric == "conversations":
        result = await db.execute(
            select(
                func.date(ConversationAnalytics.started_at).label("date"),
                func.count(ConversationAnalytics.id).label("count")
            ).where(
                ConversationAnalytics.started_at >= start_date,
                ConversationAnalytics.started_at <= end_date
            ).group_by(func.date(ConversationAnalytics.started_at)).order_by(func.date(ConversationAnalytics.started_at))
        )
        trends = [
            {"date": row[0].isoformat(), "value": row[1]}
            for row in result.all()
        ]
    
    elif metric == "csat":
        result = await db.execute(
            select(
                func.date(ConversationAnalytics.started_at).label("date"),
                func.avg(ConversationAnalytics.csat_score).label("avg_csat")
            ).where(
                ConversationAnalytics.started_at >= start_date,
                ConversationAnalytics.started_at <= end_date,
                ConversationAnalytics.csat_score.isnot(None)
            ).group_by(func.date(ConversationAnalytics.started_at)).order_by(func.date(ConversationAnalytics.started_at))
        )
        trends = [
            {"date": row[0].isoformat(), "value": round(row[1], 2)}
            for row in result.all()
        ]
    
    elif metric == "topics":
        result = await db.execute(
            select(
                func.date(TopicAnalytics.date).label("date"),
                TopicAnalytics.topic_category,
                func.sum(TopicAnalytics.count).label("count")
            ).where(
                TopicAnalytics.date >= start_date,
                TopicAnalytics.date <= end_date
            ).group_by(func.date(TopicAnalytics.date), TopicAnalytics.topic_category).order_by(func.date(TopicAnalytics.date))
        )
        # Group by date
        trends_by_date = {}
        for row in result.all():
            date_str = row[0].isoformat()
            if date_str not in trends_by_date:
                trends_by_date[date_str] = {}
            trends_by_date[date_str][row[1]] = row[2]
        
        trends = [
            {"date": date, **topics}
            for date, topics in trends_by_date.items()
        ]
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")
    
    return {
        "metric": metric,
        "time_range": time_range,
        "trends": trends
    }


@router.get("/sentiment-distribution")
async def get_sentiment_distribution(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get sentiment distribution (positive/neutral/negative)."""
    start_date, end_date = parse_time_range(time_range)
    
    # Categorize sentiment scores
    # sentiment_score > 0.1 = positive
    # sentiment_score < -0.1 = negative
    # else = neutral
    
    positive_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.sentiment_score > 0.1
        )
    )
    positive_count = positive_result.scalar() or 0
    
    negative_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.sentiment_score < -0.1
        )
    )
    negative_count = negative_result.scalar() or 0
    
    neutral_result = await db.execute(
        select(func.count(ConversationAnalytics.id)).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.sentiment_score.isnot(None),
            ConversationAnalytics.sentiment_score >= -0.1,
            ConversationAnalytics.sentiment_score <= 0.1
        )
    )
    neutral_count = neutral_result.scalar() or 0
    
    total = positive_count + negative_count + neutral_count
    
    return {
        "distribution": [
            {"sentiment": "Positive", "count": positive_count, "percentage": round((positive_count / total * 100), 1) if total > 0 else 0},
            {"sentiment": "Neutral", "count": neutral_count, "percentage": round((neutral_count / total * 100), 1) if total > 0 else 0},
            {"sentiment": "Negative", "count": negative_count, "percentage": round((negative_count / total * 100), 1) if total > 0 else 0},
        ],
        "total": total,
        "time_range": time_range
    }


@router.get("/tool-usage")
async def get_tool_usage(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get tool usage frequency and statistics."""
    start_date, end_date = parse_time_range(time_range)
    
    # Get all conversations with tools_used
    result = await db.execute(
        select(ConversationAnalytics.tools_used).where(
            ConversationAnalytics.started_at >= start_date,
            ConversationAnalytics.started_at <= end_date,
            ConversationAnalytics.tools_used.isnot(None)
        )
    )
    conversations = result.scalars().all()
    
    # Count tool usage
    tool_counts: dict[str, int] = {}
    for tools_list in conversations:
        if tools_list:
            for tool in tools_list:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
    
    # Sort by count descending
    sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "tools": [
            {"tool_name": tool, "count": count, "percentage": round((count / len(conversations) * 100), 1) if conversations else 0}
            for tool, count in sorted_tools
        ],
        "total_conversations_with_tools": len(conversations),
        "time_range": time_range
    }


@router.get("/csat-distribution")
async def get_csat_distribution(
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    db: AsyncSession = Depends(get_db)
):
    """Get CSAT score distribution (how many 1s, 2s, 3s, 4s, 5s)."""
    start_date, end_date = parse_time_range(time_range)
    
    # Count CSAT scores by rating
    csat_distribution = {}
    for rating in [1, 2, 3, 4, 5]:
        result = await db.execute(
            select(func.count(ConversationAnalytics.id)).where(
                ConversationAnalytics.started_at >= start_date,
                ConversationAnalytics.started_at <= end_date,
                ConversationAnalytics.csat_score == rating
            )
        )
        csat_distribution[rating] = result.scalar() or 0
    
    total_ratings = sum(csat_distribution.values())
    
    return {
        "distribution": [
            {"rating": rating, "count": csat_distribution[rating], "percentage": round((csat_distribution[rating] / total_ratings * 100), 1) if total_ratings > 0 else 0}
            for rating in [5, 4, 3, 2, 1]  # Order from 5 to 1
        ],
        "total_ratings": total_ratings,
        "time_range": time_range
    }


@router.post("/rating")
async def submit_rating(
    session_id: str,
    rating: int,
    comment: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Submit a CSAT rating for a conversation."""
    from analytics.event_collector import track_rating
    
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    await track_rating(db, session_id, rating, comment)
    
    return {
        "success": True,
        "message": "Rating submitted successfully"
    }
