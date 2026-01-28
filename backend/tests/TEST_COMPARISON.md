# Test Script Comparison

## Overview

We have **three different testing approaches** depending on your needs:

| Script | API Calls | Purpose | Best For |
|--------|-----------|---------|----------|
| `load_test_real_interactions.py` | ✅ **YES** | Test actual agent behavior | Validation, E2E testing |
| `load_test_support.py` | ❌ **NO** | Test analytics tracking | Load testing, CI/CD |
| `seed_analytics.py` | ❌ **NO** | Generate demo data | Presentations, demos |

## Detailed Comparison

### 1. Real Interaction Test ⚠️ **USES API CREDITS**

**File**: `load_test_real_interactions.py`

**What it does:**
- Opens real WebSocket connections
- Sends actual messages to the agent
- Makes real LLM API calls (Anthropic/OpenAI)
- Executes actual tools (database queries, etc.)
- Tests full end-to-end flow

**When to use:**
- ✅ Testing agent responses
- ✅ Validating tool execution
- ✅ End-to-end testing
- ✅ Verifying LLM integration
- ✅ Performance testing with real APIs

**Cost:**
- Each scenario = 1-3 API calls
- `--safe` mode = ~3 calls total
- Full test = ~8-15 calls total

**Example:**
```bash
# Safe mode (recommended first run)
python -m tests.load_test_real_interactions --safe

# Test 5 scenarios
python -m tests.load_test_real_interactions --scenarios 5
```

### 2. Analytics-Only Test ✅ **NO API CREDITS**

**File**: `load_test_support.py`

**What it does:**
- Simulates conversations in database
- Tests analytics event tracking
- Verifies database operations
- Tests conversation lifecycle
- **Does NOT call LLM APIs**

**When to use:**
- ✅ Testing analytics tracking
- ✅ Load testing (many iterations)
- ✅ CI/CD pipelines
- ✅ Database performance testing
- ✅ When you want to avoid API costs

**Cost:**
- **FREE** - No API calls

**Example:**
```bash
# Test 50 conversations
python -m tests.load_test_support --conversations 50 --concurrent 10
```

### 3. Demo Data Seeding ✅ **NO API CREDITS**

**File**: `data/seed_analytics.py`

**What it does:**
- Creates historical analytics data
- Generates realistic distributions
- Populates dashboard with demo data
- **Does NOT call LLM APIs**

**When to use:**
- ✅ Preparing dashboard demos
- ✅ Creating presentation data
- ✅ Testing dashboard visualizations
- ✅ Generating sample data

**Cost:**
- **FREE** - No API calls

**Example:**
```bash
# Generate 7 days of data
python -m data.seed_analytics --days 7 --per-day 15
```

## Recommended Workflow

### For Development/Testing:
1. **Start with real interactions** (small scale):
   ```bash
   python -m tests.load_test_real_interactions --safe
   ```

2. **Then test analytics** (larger scale):
   ```bash
   python -m tests.load_test_support --conversations 20
   ```

### For Presentations/Demos:
1. **Generate demo data**:
   ```bash
   python -m data.seed_analytics --days 7 --per-day 15
   ```

2. **Optionally add real test data**:
   ```bash
   python -m tests.load_test_real_interactions --safe
   ```

3. **View dashboard** at `/analytics`

## Cost Comparison

| Test Type | Scenarios | API Calls | Estimated Cost* |
|-----------|-----------|-----------|-----------------|
| Real (safe) | 3 | ~3-5 | $0.01-0.05 |
| Real (full) | 8 | ~10-20 | $0.05-0.20 |
| Analytics-only | 50 | 0 | $0.00 |
| Demo data | N/A | 0 | $0.00 |

*Costs are estimates and vary by provider/pricing

## Which Should You Use?

**"I want to test if the agent actually works"**
→ Use `load_test_real_interactions.py --safe`

**"I want to test analytics without spending money"**
→ Use `load_test_support.py`

**"I need data for a presentation"**
→ Use `seed_analytics.py`

**"I want to do both"**
→ Run real test first (small), then generate demo data
