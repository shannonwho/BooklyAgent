"""Agent controller for handling chat interactions with Claude."""
import os
import json
from typing import AsyncGenerator, Optional
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from .prompts import get_system_prompt
from .tools import TOOLS, execute_tool


class AgentController:
    """Controls the AI agent for customer support."""

    def __init__(self, session_id: str, db: Optional[AsyncSession] = None):
        self.session_id = session_id
        self.db = db
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"
        self.conversation_history: list[dict] = []
        self.user_email: Optional[str] = None
        self.user_name: Optional[str] = None
        self.max_turns = 10  # Max tool use turns to prevent infinite loops

    def set_user_context(self, email: Optional[str], name: Optional[str] = None):
        """Set the user context for personalization."""
        self.user_email = email
        self.user_name = name

    async def process_message(
        self,
        user_message: str,
        user_email: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """Process a user message and stream the response."""

        # Update user context if provided
        if user_email:
            self.user_email = user_email

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Get system prompt with context
        system_prompt = get_system_prompt(
            user_email=self.user_email,
            user_name=self.user_name
        )

        # Initial API call
        turn_count = 0

        while turn_count < self.max_turns:
            turn_count += 1

            try:
                # Make streaming API call
                async with self.client.messages.stream(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    tools=TOOLS,
                    messages=self.conversation_history,
                ) as stream:
                    assistant_content = []
                    current_text = ""

                    async for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "text":
                                current_text = ""
                            elif event.content_block.type == "tool_use":
                                # Tool use starting
                                yield {
                                    "type": "tool_use",
                                    "tool": event.content_block.name,
                                }

                        elif event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                current_text += event.delta.text
                                yield {
                                    "type": "content",
                                    "content": event.delta.text,
                                }

                        elif event.type == "content_block_stop":
                            pass

                    # Get final message
                    response = await stream.get_final_message()

                # Process the response
                assistant_content = response.content

                # Add assistant message to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Check if we need to handle tool use
                tool_uses = [
                    block for block in assistant_content
                    if block.type == "tool_use"
                ]

                if not tool_uses:
                    # No tool use, we're done
                    break

                # Execute tools and add results
                tool_results = []
                for tool_use in tool_uses:
                    yield {
                        "type": "tool_use",
                        "tool": tool_use.name,
                    }

                    # Execute the tool
                    if not self.db:
                        yield {
                            "type": "error",
                            "content": "Database session not available. Please try again.",
                        }
                        break

                    # Auto-inject user_email into tool input if tool accepts email and agent has it
                    tool_input = dict(tool_use.input) if isinstance(tool_use.input, dict) else {}
                    # Tools that typically need email parameter
                    tools_that_need_email = ["search_orders", "get_customer_info", "initiate_return", "create_support_ticket", "get_recommendations"]

                    # Inject user_email if:
                    # 1. Agent has user_email set
                    # 2. Tool needs email (either email field exists in input or tool is in list)
                    # 3. Email is not already provided or is empty/None
                    if self.user_email and tool_use.name in tools_that_need_email:
                        current_email = tool_input.get("email")
                        if not current_email:  # None, empty string, or missing
                            tool_input["email"] = self.user_email
                    # Also inject for get_order_status if email field exists but is empty
                    elif self.user_email and tool_use.name == "get_order_status" and "email" in tool_input and not tool_input.get("email"):
                        tool_input["email"] = self.user_email

                    result = await execute_tool(
                        tool_use.name,
                        tool_input,
                        self.db
                    )

                    yield {
                        "type": "tool_result",
                        "tool": tool_use.name,
                    }

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result),
                    })

                # Add tool results to history
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue loop to get next response with tool results

            except anthropic.APIError as e:
                yield {
                    "type": "error",
                    "content": f"I apologize, but I'm having trouble processing your request. Please try again.",
                }
                break

        # Trim conversation history if too long (keep system + last 20 messages)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    async def get_greeting(self) -> str:
        """Get a greeting message for new conversations."""
        if self.user_name:
            return f"Hello {self.user_name}! Welcome to Bookly support. How can I help you today?"
        elif self.user_email:
            return "Hello! Welcome to Bookly support. How can I help you today?"
        else:
            return "Hello! Welcome to Bookly support. I'm here to help with orders, returns, book recommendations, and any questions about our store. How can I assist you today?"

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
