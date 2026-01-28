"""Load test with REAL agent interactions via WebSocket.

This script makes actual API calls to test the full agent-customer interaction.
Use with caution - it will consume API credits!

Features:
- Real WebSocket connections
- Actual LLM API calls
- Configurable limits to control costs
- Tests all support scenarios
"""
import asyncio
import json
import random
import uuid
import websockets
from datetime import datetime
from typing import List, Dict, Optional


# Real support scenarios to test
REAL_SCENARIOS = [
    {
        "name": "Order Status Inquiry",
        "messages": [
            "Hi, I want to check the status of my order ORD-2024-00001",
        ],
        "expected_tools": ["get_order_status"],
    },
    {
        "name": "Order Search",
        "messages": [
            "Can you show me all my orders?",
        ],
        "expected_tools": ["search_orders"],
    },
    {
        "name": "Return Request",
        "messages": [
            "I need to return my order ORD-2024-00001, it arrived damaged",
        ],
        "expected_tools": ["get_order_status", "initiate_return"],
    },
    {
        "name": "Product Recommendation",
        "messages": [
            "Can you recommend some books for me?",
        ],
        "expected_tools": ["get_customer_info", "get_recommendations"],
    },
    {
        "name": "Book Search",
        "messages": [
            "Do you have any books by Stephen King?",
        ],
        "expected_tools": ["search_books"],
    },
    {
        "name": "Policy Question",
        "messages": [
            "What's your return policy?",
        ],
        "expected_tools": ["get_policy_info"],
    },
    {
        "name": "Account Info",
        "messages": [
            "Can you tell me about my account?",
        ],
        "expected_tools": ["get_customer_info"],
    },
    {
        "name": "Multi-turn Conversation",
        "messages": [
            "Hi, I have a question about my order",
            "The order number is ORD-2024-00001",
            "When will it arrive?",
        ],
        "expected_tools": ["get_order_status"],
    },
]


class WebSocketClient:
    """WebSocket client for testing agent interactions."""
    
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"test-{uuid.uuid4().hex[:12]}"
        self.ws = None
        self.messages_received = []
        self.tools_used = []
        self.connected = False
        
    async def connect(self, user_email: Optional[str] = None):
        """Connect to WebSocket."""
        ws_url = f"{self.base_url}/ws/chat/{self.session_id}"
        try:
            self.ws = await websockets.connect(ws_url)
            self.connected = True
            
            # Set user if provided
            if user_email:
                await self.send({"type": "set_user", "user_email": user_email})
            
            # Wait for connected message
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            print(f"  ✗ Connection failed: {e}")
            return False
    
    async def send(self, message: dict):
        """Send a message."""
        if not self.connected or not self.ws:
            return False
        try:
            await self.ws.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"  ✗ Send failed: {e}")
            return False
    
    async def receive_messages(self, timeout: float = 30.0):
        """Receive messages until conversation completes."""
        if not self.connected or not self.ws:
            return []
        
        messages = []
        start_time = asyncio.get_event_loop().time()
        
        try:
            while True:
                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    print(f"  ⚠ Timeout after {timeout}s")
                    break
                
                # Set a shorter timeout for individual receives
                try:
                    message_str = await asyncio.wait_for(
                        self.ws.recv(),
                        timeout=5.0
                    )
                    message = json.loads(message_str)
                    messages.append(message)
                    
                    # Track tool usage
                    if message.get("type") == "tool_use":
                        self.tools_used.append(message.get("tool"))
                    
                    # Check if conversation is complete
                    if message.get("type") == "message_complete":
                        break
                    if message.get("type") == "error":
                        print(f"  ⚠ Error received: {message.get('message')}")
                        break
                        
                except asyncio.TimeoutError:
                    # No message received, check if we should continue waiting
                    if messages and messages[-1].get("type") == "message_complete":
                        break
                    continue
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"  ⚠ Connection closed")
        except Exception as e:
            print(f"  ✗ Receive error: {e}")
        
        return messages
    
    async def send_message(self, content: str, user_email: Optional[str] = None):
        """Send a user message and wait for response."""
        success = await self.send({
            "type": "message",
            "content": content,
            "user_email": user_email
        })
        if not success:
            return []
        
        return await self.receive_messages()
    
    async def close(self):
        """Close the connection."""
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
        self.connected = False


async def test_scenario(
    scenario: Dict,
    user_email: Optional[str] = None,
    base_url: str = "ws://localhost:8000"
) -> Dict:
    """Test a single support scenario."""
    client = WebSocketClient(base_url)
    
    try:
        # Connect
        connected = await client.connect(user_email)
        if not connected:
            return {
                "scenario": scenario["name"],
                "success": False,
                "error": "Connection failed"
            }
        
        # Send messages
        all_responses = []
        for message in scenario["messages"]:
            print(f"    → User: {message[:60]}...")
            responses = await client.send_message(message, user_email)
            all_responses.extend(responses)
            
            # Small delay between messages
            await asyncio.sleep(1)
        
        # Extract agent response
        agent_responses = [
            r.get("content", "") for r in all_responses 
            if r.get("type") == "stream" or r.get("type") == "message"
        ]
        agent_text = " ".join(agent_responses)
        
        # Check if expected tools were used
        tools_found = [tool for tool in scenario.get("expected_tools", []) 
                      if tool in client.tools_used]
        
        success = len(tools_found) > 0 or len(scenario.get("expected_tools", [])) == 0
        
        return {
            "scenario": scenario["name"],
            "success": success,
            "tools_used": client.tools_used,
            "expected_tools": scenario.get("expected_tools", []),
            "tools_found": tools_found,
            "response_length": len(agent_text),
            "has_response": len(agent_text) > 0,
            "session_id": client.session_id,
        }
        
    except Exception as e:
        return {
            "scenario": scenario["name"],
            "success": False,
            "error": str(e)
        }
    finally:
        await client.close()


async def run_load_test(
    scenarios: List[Dict] = None,
    user_emails: List[str] = None,
    base_url: str = "ws://localhost:8000",
    max_concurrent: int = 3,
    delay_between: float = 2.0
):
    """Run load test with real agent interactions.
    
    Args:
        scenarios: List of scenarios to test (defaults to all)
        user_emails: List of user emails to use (optional)
        base_url: WebSocket base URL
        max_concurrent: Maximum concurrent connections
        delay_between: Delay between scenarios (seconds)
    """
    if scenarios is None:
        scenarios = REAL_SCENARIOS
    
    if user_emails is None:
        user_emails = [
            "sarah.johnson@email.com",
            "mike.chen@email.com",
            "emma.wilson@email.com",
        ]
    
    print(f"\n🚀 Starting REAL Agent Load Test")
    print(f"   Scenarios: {len(scenarios)}")
    print(f"   Max concurrent: {max_concurrent}")
    print(f"   ⚠️  WARNING: This will make REAL API calls and consume credits!")
    print()
    
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_limit(scenario, index):
        """Run scenario with concurrency limit."""
        async with semaphore:
            user_email = random.choice(user_emails) if user_emails else None
            print(f"  [{index+1}/{len(scenarios)}] Testing: {scenario['name']}")
            result = await test_scenario(scenario, user_email, base_url)
            results.append(result)
            
            if result["success"]:
                tools_info = f" (tools: {', '.join(result.get('tools_used', []))})"
                print(f"    ✓ Success{tools_info}")
            else:
                error = result.get("error", "Unknown error")
                print(f"    ✗ Failed: {error}")
            
            # Delay between scenarios
            if index < len(scenarios) - 1:
                await asyncio.sleep(delay_between)
    
    # Run all scenarios
    tasks = [
        run_with_limit(scenario, i)
        for i, scenario in enumerate(scenarios)
    ]
    
    await asyncio.gather(*tasks)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Total scenarios: {len(results)}")
    print(f"   Successful: {sum(1 for r in results if r.get('success'))}")
    print(f"   Failed: {sum(1 for r in results if not r.get('success'))}")
    
    # Tool usage summary
    all_tools = []
    for r in results:
        all_tools.extend(r.get("tools_used", []))
    
    if all_tools:
        from collections import Counter
        tool_counts = Counter(all_tools)
        print(f"\n   Tool usage:")
        for tool, count in tool_counts.most_common():
            print(f"     {tool}: {count}")
    
    return results


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Load test with REAL agent interactions (uses API credits!)"
    )
    parser.add_argument(
        "--scenarios",
        type=int,
        default=None,
        help="Number of scenarios to test (default: all)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=3,
        help="Max concurrent connections (default: 3)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between scenarios in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="ws://localhost:8000",
        help="WebSocket base URL (default: ws://localhost:8000)"
    )
    parser.add_argument(
        "--safe",
        action="store_true",
        help="Safe mode: only test 3 scenarios to minimize API usage"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("REAL Agent Interaction Load Test")
    print("=" * 70)
    print("⚠️  WARNING: This makes REAL API calls and WILL consume credits!")
    print("=" * 70)
    
    # Select scenarios
    scenarios_to_test = REAL_SCENARIOS
    
    if args.safe:
        scenarios_to_test = REAL_SCENARIOS[:3]
        print(f"\n🛡️  Safe mode: Testing only {len(scenarios_to_test)} scenarios")
    elif args.scenarios:
        scenarios_to_test = REAL_SCENARIOS[:args.scenarios]
        print(f"\n📝 Testing {len(scenarios_to_test)} scenarios")
    
    print(f"\n💡 Tip: Use --safe flag to minimize API usage")
    print(f"   Or specify --scenarios N to test only N scenarios\n")
    
    try:
        input("Press Enter to continue or Ctrl+C to cancel...")
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    await run_load_test(
        scenarios=scenarios_to_test,
        base_url=args.url,
        max_concurrent=args.concurrent,
        delay_between=args.delay
    )
    
    print("\n✅ Load test completed!")
    print("💡 Check your analytics dashboard to see the tracked conversations")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
