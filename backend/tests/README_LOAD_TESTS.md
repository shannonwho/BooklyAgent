# Load Tests and Demo Data Seeding

This directory contains scripts for testing customer support scenarios and generating demo data for the analytics dashboard.

## Overview

### 1. Real Interaction Load Test (`load_test_real_interactions.py`) ⚠️ **USES API CREDITS**
Tests **actual agent-customer interactions** via WebSocket:
- Real WebSocket connections
- Actual LLM API calls (Anthropic/OpenAI)
- Full agent tool execution
- End-to-end conversation flow
- **⚠️ Consumes API credits - use with caution!**

### 2. Analytics-Only Load Test (`load_test_support.py`)
Simulates customer support conversations **without making LLM API calls**. This tests:
- Analytics event tracking
- Database operations
- Conversation lifecycle management
- Tool usage tracking
- Sentiment analysis
- CSAT rating collection
- **✅ No API credits used**

### 3. Demo Data Seeding (`../data/seed_analytics.py`)
Creates realistic analytics data for dashboard demos **without using API credits**. Generates:
- Historical conversation data
- Topic distributions
- Sentiment scores
- CSAT ratings
- Resolution and escalation metrics
- **✅ No API credits used**

## Usage

### Real Agent Interaction Testing ⚠️ **USES API CREDITS**

Test actual agent-customer interactions:

```bash
# Safe mode (only 3 scenarios, minimal API usage)
cd backend
python -m tests.load_test_real_interactions --safe

# Test specific number of scenarios
python -m tests.load_test_real_interactions --scenarios 5 --concurrent 2

# Full test (all scenarios)
python -m tests.load_test_real_interactions --concurrent 3 --delay 2.0
```

**Options:**
- `--safe`: Test only 3 scenarios (recommended for first run)
- `--scenarios N`: Test only N scenarios
- `--concurrent N`: Max concurrent connections (default: 3)
- `--delay N`: Seconds between scenarios (default: 2.0)
- `--url URL`: WebSocket URL (default: ws://localhost:8000)

**⚠️ WARNING**: This makes REAL API calls and will consume credits!

### Analytics-Only Load Testing ✅ **NO API CREDITS**

Run load tests to verify analytics tracking:

```bash
# Basic test (20 conversations, 5 concurrent)
cd backend
python -m tests.load_test_support

# Custom test (50 conversations, 10 concurrent)
python -m tests.load_test_support --conversations 50 --concurrent 10
```

**Note**: This does NOT make LLM API calls - it only tests analytics tracking.

### Demo Data Seeding

Generate demo data for your dashboard presentation:

```bash
# Generate 30 days of data (10 conversations per day)
cd backend
python -m data.seed_analytics

# Generate 7 days with more conversations per day
python -m data.seed_analytics --days 7 --per-day 20
```

**Note**: This creates data directly in the database without making API calls.

## Test Scenarios

Both load tests include these common support scenarios:

1. **Order Status Inquiry** - Checking order status (`get_order_status`)
2. **Order Search** - Finding all orders (`search_orders`)
3. **Return Request** - Initiating a return (`initiate_return`)
4. **Product Recommendation** - Getting book recommendations (`get_recommendations`)
5. **Book Search** - Searching for books (`search_books`)
6. **Policy Question** - Asking about policies (`get_policy_info`)
7. **Account Info** - Getting account information (`get_customer_info`)
8. **Multi-turn Conversation** - Complex multi-message interaction

## Which Test Should I Use?

### Use Real Interaction Test (`load_test_real_interactions.py`) when:
- ✅ You want to test actual agent behavior
- ✅ You need to verify LLM responses
- ✅ You're testing tool execution
- ✅ You want end-to-end validation
- ⚠️ You're okay using API credits

### Use Analytics-Only Test (`load_test_support.py`) when:
- ✅ You want to test analytics tracking
- ✅ You need to verify database operations
- ✅ You're testing without API costs
- ✅ You want to run many iterations
- ✅ You're preparing demo data

### Use Demo Data Seeding (`seed_analytics.py`) when:
- ✅ You need dashboard demo data
- ✅ You want historical data quickly
- ✅ You're preparing for presentations
- ✅ You want realistic distributions

## Demo Data Features

The seed script creates realistic data with:
- **Topic Distribution**: Order Status (35%), Product Info (25%), Returns (15%), etc.
- **Sentiment Distribution**: Positive (40%), Neutral (45%), Negative (15%)
- **Resolution Rate**: ~85% resolved, ~15% escalated
- **CSAT Scores**: Correlated with sentiment (positive = 4-5, negative = 1-3)
- **Time Distribution**: More conversations on weekdays than weekends

## Quick Start for Demo

1. **Seed demo data** (no API calls):
   ```bash
   cd backend
   python -m data.seed_analytics --days 7 --per-day 15
   ```

2. **Start your backend**:
   ```bash
   uvicorn main:app --reload
   ```

3. **View dashboard**:
   Navigate to `http://localhost:3000/analytics` (or your frontend URL)

## Tips

- Start with small numbers (`--days 7 --per-day 10`) to avoid overwhelming the database
- The seed script uses existing customers from your database
- Load tests can run concurrently without affecting each other
- Both scripts are safe to run multiple times (they create new sessions)
