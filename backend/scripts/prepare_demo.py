#!/usr/bin/env python3
"""Prepare demo data for analytics dashboard.

This script seeds analytics data and runs a small load test
without making any LLM API calls.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.seed_analytics import seed_analytics_data
from tests.load_test_support import run_load_test


async def main():
    """Main entry point."""
    print("🚀 Preparing Analytics Dashboard Demo Data")
    print("=" * 50)
    print()
    print("This script will:")
    print("  1. Seed analytics data (no API calls)")
    print("  2. Run a small load test to verify tracking")
    print()
    
    try:
        input("Press Enter to continue or Ctrl+C to cancel...")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    print()
    print("📊 Step 1: Seeding demo analytics data...")
    await seed_analytics_data(days_back=7, conversations_per_day=12)
    
    print()
    print("🧪 Step 2: Running load test (verifying tracking)...")
    await run_load_test(num_conversations=10, concurrent_users=3)
    
    print()
    print("✅ Demo data ready!")
    print()
    print("Next steps:")
    print("  1. Start your backend: uvicorn main:app --reload")
    print("  2. Start your frontend: npm run dev")
    print("  3. Navigate to: http://localhost:3000/analytics")
    print()


if __name__ == "__main__":
    asyncio.run(main())
