# Quick Start Guide for Testing

## 🎯 Quick Decision Tree

**Want to test REAL agent interactions?**
→ Use `load_test_real_interactions.py` (⚠️ uses API credits)

**Want to test analytics without API calls?**
→ Use `load_test_support.py` (✅ no API credits)

**Want demo data for dashboard?**
→ Use `seed_analytics.py` (✅ no API credits)

## 🚀 Recommended Workflow

### Step 1: Test Real Interactions (Small Scale)
```bash
cd backend

# Start your backend first!
uvicorn main:app --reload

# In another terminal, run safe test (only 3 scenarios)
python -m tests.load_test_real_interactions --safe
```

This will:
- Make 3 real API calls
- Test actual agent responses
- Verify tool execution
- Track analytics automatically

### Step 2: Generate Demo Data
```bash
# Generate 7 days of demo data (no API calls)
python -m data.seed_analytics --days 7 --per-day 15
```

### Step 3: View Dashboard
Navigate to `http://localhost:3000/analytics` to see:
- Real test data from Step 1
- Demo data from Step 2
- Combined analytics

## 💡 Tips

1. **Start Small**: Always use `--safe` flag first
2. **Monitor Credits**: Check your API usage dashboard
3. **Use Demo Data**: For presentations, use `seed_analytics.py`
4. **Combine**: Use real tests for validation, demo data for demos

## 📊 Cost Estimation

**Real Interaction Test:**
- `--safe`: ~3 API calls (very cheap)
- `--scenarios 5`: ~5 API calls (cheap)
- Full test: ~8 API calls (moderate)

**Demo Data:**
- Always free (no API calls)

## 🔧 Troubleshooting

**"Connection refused"**
→ Make sure backend is running (`uvicorn main:app --reload`)

**"No API key"**
→ Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` environment variable

**"No customers found"**
→ Run seed scripts first: `python -m data.seed_users`
