"""Agent controller for handling chat interactions with Claude or OpenAI."""
import os
import json
import time
import re
import asyncio
from contextlib import nullcontext
from typing import AsyncGenerator, Optional, Literal
import anthropic
import openai
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from sqlalchemy.ext.asyncio import AsyncSession

from .prompts import get_system_prompt
from .tools import TOOLS, execute_tool
from telemetry import (
    get_tracer,
    get_logger,
    get_meter,
    trace_tool_execution,
    log_conversation,
    record_fallback_event,
    is_telemetry_enabled,
)
from analytics.event_collector import (
    track_conversation_start,
    track_tool_usage,
    track_sentiment,
)
from data.database import AsyncSessionLocal

# Pattern to extract order numbers from messages
ORDER_ID_PATTERN = re.compile(r'ORD-\d{4}-\d{5}', re.IGNORECASE)


def _safe_debug_log(data: dict):
    """Safely write debug log without crashing if directory doesn't exist."""
    try:
        log_path = '/Users/shannonhu/Documents/Empire/JobInterview/Cursor/BooklyAgent/.cursor/debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps(data) + '\n')
    except Exception:
        pass  # Silently fail if logging isn't available


# Convert Claude tools format to OpenAI format
def convert_tools_to_openai(claude_tools: list) -> list:
    """Convert Claude tool definitions to OpenAI function format."""
    openai_tools = []
    for tool in claude_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        })
    return openai_tools


OPENAI_TOOLS = convert_tools_to_openai(TOOLS)


class AgentController:
    """Controls the AI agent for customer support with Anthropic/OpenAI fallback."""

    def __init__(self, session_id: str, db: Optional[AsyncSession] = None):
        self.session_id = session_id
        self.db = db
        self.tracer = get_tracer()
        self.logger = get_logger()
        self.meter = get_meter()

        # Initialize clients
        self.anthropic_client = None
        self.openai_client = None
        self.active_provider: Literal["anthropic", "openai"] = "anthropic"

        # Try to initialize Anthropic client
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_key)

        # Try to initialize OpenAI client
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = openai.AsyncOpenAI(api_key=openai_key)

        # Models
        self.anthropic_model = "claude-sonnet-4-20250514"
        self.openai_model = "gpt-4o"

        self.conversation_history: list[dict] = []
        self.openai_messages: list[dict] = []
        self.user_email: Optional[str] = None
        self.user_name: Optional[str] = None
        self.max_turns = 10
        self.turn_count = 0

        # Context tracking for multi-turn conversations
        self.current_order_id: Optional[str] = None
        
        # Track tools used for analytics
        self.tools_used: list[str] = []

        # Metrics
        self._setup_metrics()

    def _setup_metrics(self):
        """Set up telemetry metrics."""
        # Skip metric creation if telemetry is disabled
        if not is_telemetry_enabled():
            # Create no-op metrics
            class NoOpMetric:
                def add(self, *args, **kwargs):
                    pass
                def record(self, *args, **kwargs):
                    pass
            self.message_counter = NoOpMetric()
            self.response_latency = NoOpMetric()
            self.token_counter = NoOpMetric()
            return
        
        self.message_counter = self.meter.create_counter(
            "agent.messages.total",
            description="Total messages processed by the agent",
            unit="1"
        )
        self.response_latency = self.meter.create_histogram(
            "agent.response.latency",
            description="Agent response latency",
            unit="ms"
        )
        self.token_counter = self.meter.create_counter(
            "agent.tokens.total",
            description="Total tokens used",
            unit="1"
        )

    def set_user_context(self, email: Optional[str], name: Optional[str] = None):
        """Set the user context for personalization."""
        self.user_email = email
        self.user_name = name

    def _extract_order_id(self, message: str) -> Optional[str]:
        """Extract order ID from a message if present."""
        match = ORDER_ID_PATTERN.search(message)
        if match:
            return match.group(0).upper()
        return None

    def _inject_order_context(self, tool_name: str, tool_input: dict) -> dict:
        """Inject current order context into tool input if needed."""
        tools_that_need_order = ["get_order_status", "initiate_return"]
        if tool_name in tools_that_need_order:
            if not tool_input.get("order_id") and self.current_order_id:
                tool_input["order_id"] = self.current_order_id
        return tool_input

    def _should_fallback_to_openai(self, error: Exception) -> bool:
        """Check if we should fallback to OpenAI based on the error."""
        error_message = str(error).lower()
        billing_keywords = ["credit", "balance", "billing", "payment", "insufficient"]
        if any(keyword in error_message for keyword in billing_keywords):
            return True
        if isinstance(error, anthropic.APIStatusError):
            if error.status_code in [400, 401, 403, 429, 500, 502, 503]:
                return True
        return True

    async def process_message(
        self,
        user_message: str,
        user_email: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """Process a user message and stream the response."""
        # #region agent log
        _safe_debug_log({"location":"controller.py:138","message":"process_message called","data":{"session_id":self.session_id,"user_message_length":len(user_message),"user_email":user_email,"has_anthropic":bool(self.anthropic_client),"has_openai":bool(self.openai_client),"active_provider":self.active_provider},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})
        # #endregion
        start_time = time.time()
        self.turn_count += 1
        tools_used = []
        response_text = ""

        # Update user context if provided
        if user_email:
            self.user_email = user_email

        # Extract and track order ID from message
        extracted_order_id = self._extract_order_id(user_message)
        if extracted_order_id:
            self.current_order_id = extracted_order_id

        # Create parent span for entire conversation turn (no-op if telemetry disabled)
        if is_telemetry_enabled():
            span_context = self.tracer.start_as_current_span(
                "agent.process_message",
                kind=SpanKind.SERVER,
            )
        else:
            # Use nullcontext to create a no-op context manager
            class NoOpSpan:
                def set_attribute(self, *args, **kwargs):
                    pass
                def set_status(self, *args, **kwargs):
                    pass
                def add_event(self, *args, **kwargs):
                    pass
                def record_exception(self, *args, **kwargs):
                    pass
            span_context = nullcontext(NoOpSpan())
        
        with span_context as span:
            span.set_attribute("session.id", self.session_id)
            span.set_attribute("conversation.turn", self.turn_count)
            span.set_attribute("user.email", self.user_email or "anonymous")
            span.set_attribute("message.length", len(user_message))

            # Log conversation start
            log_conversation(
                session_id=self.session_id,
                event_type="message_received",
                user_email=self.user_email,
                message=user_message,
                metadata={"turn": self.turn_count}
            )
            
            # Track conversation start for analytics (only on first message) - non-blocking
            if self.turn_count == 1:
                async def track_start():
                    try:
                        async with AsyncSessionLocal() as db:
                            await track_conversation_start(db, self.session_id, self.user_email)
                    except Exception as e:
                        self.logger.warning(f"Failed to track conversation start: {e}")
                asyncio.create_task(track_start())
            
            # Track sentiment from user message - non-blocking
            async def track_user_sentiment():
                try:
                    async with AsyncSessionLocal() as db:
                        await track_sentiment(db, self.session_id, user_message)
                except Exception as e:
                    self.logger.warning(f"Failed to track sentiment: {e}")
            asyncio.create_task(track_user_sentiment())

            # Try Anthropic first if available and active
            if self.anthropic_client and self.active_provider == "anthropic":
                # #region agent log
                _safe_debug_log({"location":"controller.py:178","message":"Processing with Anthropic","data":{"session_id":self.session_id},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})
                # #endregion
                try:
                    chunk_count = 0
                    async for chunk in self._process_with_anthropic(user_message, span, tools_used):
                        chunk_count += 1
                        # #region agent log
                        _safe_debug_log({"location":"controller.py:180","message":"Yielding chunk from Anthropic","data":{"session_id":self.session_id,"chunk_type":chunk.get("type"),"chunk_count":chunk_count},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})
                        # #endregion
                        if chunk.get("type") == "content":
                            response_text += chunk.get("content", "")
                        yield chunk

                    # Log successful completion
                    # #region agent log
                    _safe_debug_log({"location":"controller.py:186","message":"Anthropic processing complete","data":{"session_id":self.session_id,"total_chunks":chunk_count,"response_length":len(response_text)},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})
                    # #endregion
                    await self._log_completion(start_time, response_text, tools_used, "anthropic", span)
                    return

                except (anthropic.APIStatusError, anthropic.APIError) as e:
                    error_str = str(e)
                    self.logger.error(f"Anthropic API error: {error_str}")
                    span.add_event("anthropic_error", {"error": error_str})

                    if self._should_fallback_to_openai(e):
                        record_fallback_event(
                            session_id=self.session_id,
                            from_provider="anthropic",
                            to_provider="openai",
                            reason=error_str[:200]
                        )
                        self.active_provider = "openai"
                        span.set_attribute("fallback.used", True)
                        span.set_attribute("fallback.reason", error_str[:100])

                        if self.conversation_history and self.conversation_history[-1].get("role") == "user":
                            self.conversation_history.pop()
                    else:
                        span.set_status(Status(StatusCode.ERROR, error_str))
                        yield {"type": "error", "content": "I apologize, but I'm having trouble processing your request."}
                        return

            # Use OpenAI as fallback or primary
            if self.openai_client and self.active_provider == "openai":
                # #region agent log
                _safe_debug_log({"location":"controller.py:213","message":"Processing with OpenAI","data":{"session_id":self.session_id},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})
                # #endregion
                try:
                    chunk_count = 0
                    async for chunk in self._process_with_openai(user_message, span, tools_used):
                        chunk_count += 1
                        # #region agent log
                        _safe_debug_log({"location":"controller.py:215","message":"Yielding chunk from OpenAI","data":{"session_id":self.session_id,"chunk_type":chunk.get("type"),"chunk_count":chunk_count},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})
                        # #endregion
                        if chunk.get("type") == "content":
                            response_text += chunk.get("content", "")
                        yield chunk

                    # #region agent log
                    _safe_debug_log({"location":"controller.py:220","message":"OpenAI processing complete","data":{"session_id":self.session_id,"total_chunks":chunk_count,"response_length":len(response_text)},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})
                    # #endregion
                    await self._log_completion(start_time, response_text, tools_used, "openai", span)
                    return

                except openai.APIError as e:
                    error_str = str(e)
                    self.logger.error(f"OpenAI API error: {error_str}")
                    span.set_status(Status(StatusCode.ERROR, error_str))
                    span.record_exception(e)

                    log_conversation(
                        session_id=self.session_id,
                        event_type="error",
                        user_email=self.user_email,
                        metadata={"error": error_str, "provider": "openai"}
                    )

                    yield {"type": "error", "content": "I apologize, but both AI providers are currently unavailable."}
                    return

            # No provider available
            # #region agent log
            _safe_debug_log({"location":"controller.py:240","message":"No provider available","data":{"session_id":self.session_id,"has_anthropic":bool(self.anthropic_client),"has_openai":bool(self.openai_client),"active_provider":self.active_provider},"timestamp":int(time.time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})
            # #endregion
            span.set_status(Status(StatusCode.ERROR, "No provider available"))
            yield {"type": "error", "content": "No AI provider configured. Please check API keys."}

    async def _log_completion(self, start_time: float, response_text: str, tools_used: list, provider: str, span):
        """Log successful message completion."""
        duration_ms = (time.time() - start_time) * 1000

        span.set_attribute("response.length", len(response_text))
        span.set_attribute("response.provider", provider)
        span.set_attribute("tools.count", len(tools_used))
        span.set_attribute("duration_ms", duration_ms)
        span.set_status(Status(StatusCode.OK))

        self.message_counter.add(1, {"provider": provider, "status": "success"})
        self.response_latency.record(duration_ms, {"provider": provider})

        log_conversation(
            session_id=self.session_id,
            event_type="message_completed",
            user_email=self.user_email,
            response=response_text,
            provider=provider,
            tools_used=tools_used,
            metadata={
                "turn": self.turn_count,
                "duration_ms": round(duration_ms, 2),
            }
        )
        
        # Track sentiment from agent response - non-blocking
        if response_text:
            async def track_agent_sentiment():
                try:
                    async with AsyncSessionLocal() as db:
                        await track_sentiment(db, self.session_id, response_text)
                except Exception as e:
                    self.logger.warning(f"Failed to track sentiment: {e}")
            asyncio.create_task(track_agent_sentiment())

    async def _process_with_anthropic(
        self,
        user_message: str,
        parent_span,
        tools_used: list
    ) -> AsyncGenerator[dict, None]:
        """Process message using Anthropic Claude."""
        self.conversation_history.append({"role": "user", "content": user_message})

        system_prompt = get_system_prompt(
            user_email=self.user_email,
            user_name=self.user_name,
            current_order_id=self.current_order_id
        )
        turn_count = 0

        while turn_count < self.max_turns:
            turn_count += 1

            with self.tracer.start_as_current_span(
                "llm.anthropic.call",
                kind=SpanKind.CLIENT,
            ) as llm_span:
                llm_span.set_attribute("llm.provider", "anthropic")
                llm_span.set_attribute("llm.model", self.anthropic_model)
                llm_span.set_attribute("llm.turn", turn_count)

                call_start = time.time()

                async with self.anthropic_client.messages.stream(
                    model=self.anthropic_model,
                    max_tokens=1024,
                    system=system_prompt,
                    tools=TOOLS,
                    messages=self.conversation_history,
                ) as stream:
                    async for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "tool_use":
                                yield {"type": "tool_use", "tool": event.content_block.name}
                        elif event.type == "content_block_delta":
                            if hasattr(event.delta, "text"):
                                yield {"type": "content", "content": event.delta.text}

                    response = await stream.get_final_message()

                call_duration = (time.time() - call_start) * 1000
                llm_span.set_attribute("duration_ms", call_duration)

                # Record token usage if available
                if hasattr(response, 'usage'):
                    llm_span.set_attribute("tokens.input", response.usage.input_tokens)
                    llm_span.set_attribute("tokens.output", response.usage.output_tokens)
                    self.token_counter.add(response.usage.input_tokens, {"type": "input", "provider": "anthropic"})
                    self.token_counter.add(response.usage.output_tokens, {"type": "output", "provider": "anthropic"})

            assistant_content = response.content
            self.conversation_history.append({"role": "assistant", "content": assistant_content})

            tool_uses = [block for block in assistant_content if block.type == "tool_use"]

            if not tool_uses:
                break

            tool_results = []
            for tool_use in tool_uses:
                tools_used.append(tool_use.name)
                if tool_use.name not in self.tools_used:
                    self.tools_used.append(tool_use.name)
                yield {"type": "tool_use", "tool": tool_use.name}

                if not self.db:
                    error_msg = "Database session not available. Please try again."
                    self.logger.error(f"Database session missing for tool {tool_use.name}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps({"error": error_msg}),
                    })
                    yield {"type": "tool_result", "tool": tool_use.name}
                    continue

                tool_input = dict(tool_use.input) if isinstance(tool_use.input, dict) else {}

                # Inject order context if available
                tool_input = self._inject_order_context(tool_use.name, tool_input)

                # Inject email context if available
                tools_that_need_email = ["search_orders", "get_customer_info", "initiate_return", "create_support_ticket", "get_recommendations"]
                if self.user_email and tool_use.name in tools_that_need_email:
                    if not tool_input.get("email"):
                        tool_input["email"] = self.user_email
                elif self.user_email and tool_use.name == "get_order_status" and not tool_input.get("email"):
                    tool_input["email"] = self.user_email

                # Execute tool with tracing and comprehensive error handling
                success = True
                result = None
                try:
                    with trace_tool_execution(tool_use.name, self.session_id) as tool_tracer:
                        tool_tracer.set_input(tool_input)
                        try:
                            result = await execute_tool(tool_use.name, tool_input, self.db)
                            tool_tracer.set_output(result)
                            # Check if result indicates error
                            if isinstance(result, dict) and result.get("error"):
                                success = False
                                self.logger.warning(f"Tool {tool_use.name} returned error: {result.get('error')}")
                        except Exception as e:
                            success = False
                            error_msg = f"I encountered an error while {tool_use.name.replace('_', ' ')}. Please try again or rephrase your request."
                            self.logger.error(f"Tool execution failed for {tool_use.name}: {e}", exc_info=True)
                            result = {"error": error_msg, "details": str(e)}
                            tool_tracer.set_output(result)
                except Exception as e:
                    # Fallback error handling if tracing fails
                    success = False
                    error_msg = f"I encountered an error while {tool_use.name.replace('_', ' ')}. Please try again."
                    self.logger.error(f"Tool execution failed for {tool_use.name}: {e}", exc_info=True)
                    result = {"error": error_msg}
                
                # Track tool usage for analytics - non-blocking
                async def track_tool():
                    try:
                        async with AsyncSessionLocal() as db:
                            await track_tool_usage(db, self.session_id, tool_use.name, success)
                    except Exception as e:
                        self.logger.warning(f"Failed to track tool usage: {e}")
                asyncio.create_task(track_tool())

                yield {"type": "tool_result", "tool": tool_use.name}

                # Always add result to conversation, even if it's an error
                # This allows the LLM to handle the error gracefully
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result) if result else json.dumps({"error": "Unknown error occurred"}),
                })

            self.conversation_history.append({"role": "user", "content": tool_results})

        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    async def _process_with_openai(
        self,
        user_message: str,
        parent_span,
        tools_used: list
    ) -> AsyncGenerator[dict, None]:
        """Process message using OpenAI GPT."""
        system_prompt = get_system_prompt(
            user_email=self.user_email,
            user_name=self.user_name,
            current_order_id=self.current_order_id
        )

        if not self.openai_messages:
            self.openai_messages = [{"role": "system", "content": system_prompt}]
        else:
            # Update system prompt with current context (order ID may have changed)
            self.openai_messages[0] = {"role": "system", "content": system_prompt}

        self.openai_messages.append({"role": "user", "content": user_message})
        turn_count = 0

        while turn_count < self.max_turns:
            turn_count += 1

            with self.tracer.start_as_current_span(
                "llm.openai.call",
                kind=SpanKind.CLIENT,
            ) as llm_span:
                llm_span.set_attribute("llm.provider", "openai")
                llm_span.set_attribute("llm.model", self.openai_model)
                llm_span.set_attribute("llm.turn", turn_count)

                call_start = time.time()

                stream = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=self.openai_messages,
                    tools=OPENAI_TOOLS,
                    stream=True,
                )

                collected_content = ""
                tool_calls = []
                current_tool_call = None

                async for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    if delta.content:
                        collected_content += delta.content
                        yield {"type": "content", "content": delta.content}

                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            if tc.index is not None:
                                while len(tool_calls) <= tc.index:
                                    tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                                current_tool_call = tool_calls[tc.index]

                            if tc.id:
                                current_tool_call["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    current_tool_call["function"]["name"] = tc.function.name
                                    yield {"type": "tool_use", "tool": tc.function.name}
                                if tc.function.arguments:
                                    current_tool_call["function"]["arguments"] += tc.function.arguments

                call_duration = (time.time() - call_start) * 1000
                llm_span.set_attribute("duration_ms", call_duration)

            assistant_message = {"role": "assistant", "content": collected_content or None}
            if tool_calls:
                assistant_message["tool_calls"] = [
                    {"id": tc["id"], "type": "function", "function": tc["function"]}
                    for tc in tool_calls if tc["id"]
                ]
            self.openai_messages.append(assistant_message)

            if not tool_calls or not any(tc["id"] for tc in tool_calls):
                break

            for tc in tool_calls:
                if not tc["id"]:
                    continue

                tool_name = tc["function"]["name"]
                tools_used.append(tool_name)
                if tool_name not in self.tools_used:
                    self.tools_used.append(tool_name)

                try:
                    tool_input = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    tool_input = {}

                if not self.db:
                    error_msg = "Database session not available. Please try again."
                    self.logger.error(f"Database session missing for tool {tool_name}")
                    self.openai_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps({"error": error_msg}),
                    })
                    yield {"type": "tool_result", "tool": tool_name}
                    continue

                # Inject order context if available
                tool_input = self._inject_order_context(tool_name, tool_input)

                # Inject email context if available
                tools_that_need_email = ["search_orders", "get_customer_info", "initiate_return", "create_support_ticket", "get_recommendations"]
                if self.user_email and tool_name in tools_that_need_email:
                    if not tool_input.get("email"):
                        tool_input["email"] = self.user_email
                elif self.user_email and tool_name == "get_order_status" and not tool_input.get("email"):
                    tool_input["email"] = self.user_email

                # Execute tool with tracing and comprehensive error handling
                success = True
                result = None
                try:
                    with trace_tool_execution(tool_name, self.session_id) as tool_tracer:
                        tool_tracer.set_input(tool_input)
                        try:
                            result = await execute_tool(tool_name, tool_input, self.db)
                            tool_tracer.set_output(result)
                            # Check if result indicates error
                            if isinstance(result, dict) and result.get("error"):
                                success = False
                                self.logger.warning(f"Tool {tool_name} returned error: {result.get('error')}")
                        except Exception as e:
                            success = False
                            error_msg = f"I encountered an error while {tool_name.replace('_', ' ')}. Please try again or rephrase your request."
                            self.logger.error(f"Tool execution failed for {tool_name}: {e}", exc_info=True)
                            result = {"error": error_msg, "details": str(e)}
                            tool_tracer.set_output(result)
                except Exception as e:
                    # Fallback error handling if tracing fails
                    success = False
                    error_msg = f"I encountered an error while {tool_name.replace('_', ' ')}. Please try again."
                    self.logger.error(f"Tool execution failed for {tool_name}: {e}", exc_info=True)
                    result = {"error": error_msg}
                
                # Track tool usage for analytics - non-blocking
                async def track_tool():
                    try:
                        async with AsyncSessionLocal() as db:
                            await track_tool_usage(db, self.session_id, tool_name, success)
                    except Exception as e:
                        self.logger.warning(f"Failed to track tool usage: {e}")
                asyncio.create_task(track_tool())

                yield {"type": "tool_result", "tool": tool_name}

                # Always add result to conversation, even if it's an error
                # This allows the LLM to handle the error gracefully
                self.openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result) if result else json.dumps({"error": "Unknown error occurred"}),
                })

        if len(self.openai_messages) > 21:
            self.openai_messages = [self.openai_messages[0]] + self.openai_messages[-20:]

    async def get_greeting(self) -> str:
        """Get a greeting message for new conversations."""
        if self.user_name:
            return f"Hello {self.user_name}! Welcome to Bookly support. How can I help you today?"
        elif self.user_email:
            return "Hello! Welcome to Bookly support. How can I help you today?"
        else:
            return "Hello! Welcome to Bookly support. I'm here to help with orders, returns, book recommendations, and any questions about our store. How can I assist you today?"

    def reset_conversation(self):
        """Reset the conversation history and context."""
        self.conversation_history = []
        self.openai_messages = []
        self.turn_count = 0
        self.current_order_id = None
        self.tools_used = []