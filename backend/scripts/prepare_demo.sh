#!/bin/bash
# Quick script to prepare demo data for analytics dashboard

echo "🚀 Preparing Analytics Dashboard Demo Data"
echo "=========================================="
echo ""
echo "This script will:"
echo "  1. Seed analytics data (no API calls)"
echo "  2. Run a small load test to verify tracking"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

cd "$(dirname "$0")/.."

echo ""
echo "📊 Step 1: Seeding demo analytics data..."
python -m data.seed_analytics --days 7 --per-day 12

echo ""
echo "🧪 Step 2: Running load test (verifying tracking)..."
python -m tests.load_test_support --conversations 10 --concurrent 3

echo ""
echo "✅ Demo data ready!"
echo ""
echo "Next steps:"
echo "  1. Start your backend: uvicorn main:app --reload"
echo "  2. Start your frontend: npm run dev"
echo "  3. Navigate to: http://localhost:3000/analytics"
echo ""
