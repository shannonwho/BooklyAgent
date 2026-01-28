"""Load tests for customer support scenarios.

This script simulates common customer support interactions without making
actual LLM API calls to avoid using API credits. It tests the analytics
tracking and database operations.
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from data.database import AsyncSessionLocal
from analytics.event_collector import (
    track_conversation_start,
    track_conversation_end,
    track_tool_usage,
    track_sentiment,
    track_rating,
    track_event,
    get_topic_category,
)


# Common support scenarios
SUPPORT_SCENARIOS = [
    {
        "name": "Order Status Inquiry",
        "user_message": "Hi, I want to check the status of my order",
        "tools": ["get_order_status", "search_orders"],
        "sentiment": "neutral",
        "resolved": True,
        "escalated": False,
        "csat": random.randint(4, 5),
    },
    {
        "name": "Return Request",
        "user_message": "I need to return my order, it arrived damaged",
        "tools": ["get_order_status", "initiate_return"],
        "sentiment": "negative",
        "resolved": True,
        "escalated": False,
        "csat": random.randint(3, 5),
    },
    {
        "name": "Product Recommendation",
        "user_message": "Can you recommend some books for me?",
        "tools": ["get_customer_info", "get_recommendations"],
        "sentiment": "positive",
        "resolved": True,
        "escalated": False,
        "csat": random.randint(4, 5),
    },
    {
        "name": "Policy Question",
        "user_message": "What's your return policy?",
        "tools": ["get_policy_info"],
        "sentiment": "neutral",
        "resolved": True,
        "escalated": False,
        "csat": random.randint(4, 5),
    },
    {
        "name": "Book Search",
        "user_message": "Do you have any books by Stephen King?",
        "tools": ["search_books"],
        "sentiment": "neutral",
        "resolved": True,
        "escalated": False,
        "csat": random.randint(4, 5),
    },
    {
        "name": "Account Issue",
        "user_message": "I can't access my account, can you help?",
        "tools": ["get_customer_info"],
        "sentiment": "negative",
        "resolved": False,
        "escalated": True,
        "csat": random.randint(2, 4),
    },
    {
        "name": "Complex Order Issue",
        "user_message": "My order is late and I'm frustrated. I need help immediately!",
        "tools": ["get_order_status", "create_support_ticket"],
        "sentiment": "negative",
        "resolved": False,
        "escalated": True,
        "csat": random.randint(1, 3),
    },
    {
        "name": "Happy Customer",
        "user_message": "Thank you so much! The books arrived perfectly and I love them!",
        "tools": [],
        "sentiment": "positive",
        "resolved": True,
        "escalated": False,
        "csat": 5,
    },
]


async def simulate_conversation(
    db: AsyncSession,
    scenario: Dict,
    user_email: str = None,
    session_id: str = None
) -> Dict:
    """Simulate a single support conversation."""
    if not session_id:
        session_id = f"load-test-{uuid.uuid4().hex[:12]}"
    
    if not user_email:
        user_email = f"test-user-{random.randint(1, 10)}@example.com"
    
    start_time = datetime.utcnow()
    
    # Track conversation start
    await track_conversation_start(db, session_id, user_email)
    
    # Simulate message exchange
    message_count = random.randint(2, 6)
    tools_used = []
    
    for i in range(message_count):
        # Track user message
        await track_event(
            db,
            event_type="message_sent",
            session_id=session_id,
            user_email=user_email,
            metadata={"message_number": i + 1, "content": scenario["user_message"][:100]}
        )
        
        # Track sentiment
        if i == 0:  # Track sentiment from first message
            await track_sentiment(db, session_id, scenario["user_message"])
        
        # Simulate tool usage
        if scenario["tools"] and i < len(scenario["tools"]):
            tool_name = scenario["tools"][i]
            tools_used.append(tool_name)
            success = random.random() > 0.1  # 90% success rate
            await track_tool_usage(db, session_id, tool_name, success)
        
        # Small delay between messages
        await asyncio.sleep(0.1)
    
    # Track conversation end
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()
    
    await track_conversation_end(
        db,
        session_id,
        resolved=scenario["resolved"],
        escalated=scenario["escalated"]
    )
    
    # Track CSAT rating (80% of conversations get rated)
    if random.random() < 0.8:
        await track_rating(
            db,
            session_id,
            scenario["csat"],
            comment=f"Test rating for {scenario['name']}" if random.random() < 0.3 else None
        )
    
    return {
        "session_id": session_id,
        "scenario": scenario["name"],
        "duration": duration,
        "tools_used": tools_used,
        "resolved": scenario["resolved"],
        "escalated": scenario["escalated"],
    }


async def run_load_test(
    num_conversations: int = 20,
    concurrent_users: int = 5,
    user_emails: List[str] = None
):
    """Run load test with multiple concurrent conversations."""
    print(f"\n🚀 Starting load test: {num_conversations} conversations, {concurrent_users} concurrent users")
    
    if not user_emails:
        user_emails = [f"test-user-{i}@example.com" for i in range(1, 11)]
    
    results = []
    
    async def run_batch(batch_num: int, batch_size: int):
        """Run a batch of conversations."""
        batch_results = []
        async with AsyncSessionLocal() as db:
            for i in range(batch_size):
                scenario = random.choice(SUPPORT_SCENARIOS)
                user_email = random.choice(user_emails)
                
                try:
                    result = await simulate_conversation(db, scenario, user_email)
                    batch_results.append(result)
                    print(f"  ✓ Batch {batch_num}, Conversation {i+1}: {scenario['name']}")
                except Exception as e:
                    print(f"  ✗ Batch {batch_num}, Conversation {i+1} failed: {e}")
        
        return batch_results
    
    # Run conversations in batches
    batch_size = concurrent_users
    num_batches = (num_conversations + batch_size - 1) // batch_size
    
    tasks = []
    for batch_num in range(num_batches):
        current_batch_size = min(batch_size, num_conversations - batch_num * batch_size)
        if current_batch_size > 0:
            task = run_batch(batch_num + 1, current_batch_size)
            tasks.append(task)
    
    # Run batches concurrently
    batch_results = await asyncio.gather(*tasks)
    
    # Flatten results
    for batch_result in batch_results:
        results.extend(batch_result)
    
    # Print summary
    print(f"\n📊 Load Test Summary:")
    print(f"  Total conversations: {len(results)}")
    print(f"  Resolved: {sum(1 for r in results if r['resolved'])}")
    print(f"  Escalated: {sum(1 for r in results if r['escalated'])}")
    print(f"  Avg duration: {sum(r['duration'] for r in results) / len(results):.2f}s")
    
    # Count scenarios
    scenario_counts = {}
    for r in results:
        scenario = r['scenario']
        scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
    
    print(f"\n  Scenario distribution:")
    for scenario, count in sorted(scenario_counts.items(), key=lambda x: -x[1]):
        print(f"    {scenario}: {count}")
    
    return results


async def main():
    """Main entry point for load testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test customer support scenarios")
    parser.add_argument(
        "--conversations",
        type=int,
        default=20,
        help="Number of conversations to simulate (default: 20)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Number of concurrent conversations (default: 5)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Customer Support Load Test")
    print("=" * 60)
    print(f"Note: This test does NOT make LLM API calls")
    print(f"      It only tests analytics tracking and database operations")
    print("=" * 60)
    
    await run_load_test(
        num_conversations=args.conversations,
        concurrent_users=args.concurrent
    )
    
    print("\n✅ Load test completed!")


if __name__ == "__main__":
    asyncio.run(main())
