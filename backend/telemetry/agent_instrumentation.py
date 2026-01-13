"""Instrumentation utilities for the support agent."""
import json
import time
from typing import Any, Optional, Dict
from functools import wraps
from datetime import datetime

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind

from .config import get_tracer, get_logger, get_meter


# Custom semantic conventions for LLM operations
class LLMSemanticConventions:
    """Semantic conventions for LLM tracing."""
    LLM_SYSTEM = "llm.system"  # "anthropic" or "openai"
    LLM_MODEL = "llm.model"
    LLM_PROVIDER = "llm.provider"
    LLM_REQUEST_TYPE = "llm.request_type"  # "chat", "completion"
    LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
    LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"
    LLM_TEMPERATURE = "llm.temperature"
    LLM_MAX_TOKENS = "llm.max_tokens"

    # Conversation attributes
    CONVERSATION_ID = "conversation.id"
    CONVERSATION_TURN = "conversation.turn"
    USER_ID = "user.id"
    USER_EMAIL = "user.email"

    # Tool attributes
    TOOL_NAME = "tool.name"
    TOOL_INPUT = "tool.input"
    TOOL_OUTPUT = "tool.output"
    TOOL_DURATION_MS = "tool.duration_ms"

    # Quality metrics
    RESPONSE_QUALITY = "response.quality"
    RESPONSE_LENGTH = "response.length"
    ERROR_TYPE = "error.type"
    FALLBACK_USED = "fallback.used"
    FALLBACK_REASON = "fallback.reason"


def trace_llm_call(
    provider: str,
    model: str,
    session_id: str,
    user_email: Optional[str] = None,
    turn_number: int = 1
):
    """Decorator to trace LLM API calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            logger = get_logger()
            meter = get_meter()

            # Create metrics
            llm_call_counter = meter.create_counter(
                "llm.calls.total",
                description="Total number of LLM API calls",
                unit="1"
            )
            llm_latency = meter.create_histogram(
                "llm.latency",
                description="LLM API call latency",
                unit="ms"
            )
            llm_errors = meter.create_counter(
                "llm.errors.total",
                description="Total number of LLM API errors",
                unit="1"
            )

            with tracer.start_as_current_span(
                f"llm.{provider}.chat",
                kind=SpanKind.CLIENT
            ) as span:
                start_time = time.time()

                # Set span attributes
                span.set_attribute(LLMSemanticConventions.LLM_PROVIDER, provider)
                span.set_attribute(LLMSemanticConventions.LLM_MODEL, model)
                span.set_attribute(LLMSemanticConventions.CONVERSATION_ID, session_id)
                span.set_attribute(LLMSemanticConventions.CONVERSATION_TURN, turn_number)

                if user_email:
                    span.set_attribute(LLMSemanticConventions.USER_EMAIL, user_email)

                try:
                    # Execute the LLM call
                    result = await func(*args, **kwargs)

                    duration_ms = (time.time() - start_time) * 1000

                    # Record metrics
                    llm_call_counter.add(1, {"provider": provider, "model": model, "status": "success"})
                    llm_latency.record(duration_ms, {"provider": provider, "model": model})

                    span.set_attribute("duration_ms", duration_ms)
                    span.set_status(Status(StatusCode.OK))

                    # Log successful call
                    logger.info(
                        f"LLM call completed",
                        extra={
                            "provider": provider,
                            "model": model,
                            "session_id": session_id,
                            "turn": turn_number,
                            "duration_ms": round(duration_ms, 2),
                            "user_email": user_email,
                        }
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000

                    # Record error metrics
                    llm_call_counter.add(1, {"provider": provider, "model": model, "status": "error"})
                    llm_errors.add(1, {"provider": provider, "model": model, "error_type": type(e).__name__})
                    llm_latency.record(duration_ms, {"provider": provider, "model": model})

                    span.set_attribute(LLMSemanticConventions.ERROR_TYPE, type(e).__name__)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                    # Log error
                    logger.error(
                        f"LLM call failed",
                        extra={
                            "provider": provider,
                            "model": model,
                            "session_id": session_id,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "duration_ms": round(duration_ms, 2),
                        }
                    )

                    raise

        return wrapper
    return decorator


def trace_tool_execution(tool_name: str, session_id: str):
    """Context manager to trace tool execution."""
    class ToolTracer:
        def __init__(self):
            self.tracer = get_tracer()
            self.logger = get_logger()
            self.meter = get_meter()
            self.span = None
            self.start_time = None

            # Create metrics
            self.tool_counter = self.meter.create_counter(
                "tool.executions.total",
                description="Total number of tool executions",
                unit="1"
            )
            self.tool_latency = self.meter.create_histogram(
                "tool.latency",
                description="Tool execution latency",
                unit="ms"
            )

        def __enter__(self):
            self.start_time = time.time()
            self.span = self.tracer.start_span(
                f"tool.{tool_name}",
                kind=SpanKind.INTERNAL
            )
            self.span.set_attribute(LLMSemanticConventions.TOOL_NAME, tool_name)
            self.span.set_attribute(LLMSemanticConventions.CONVERSATION_ID, session_id)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type is None:
                self.span.set_status(Status(StatusCode.OK))
                self.tool_counter.add(1, {"tool": tool_name, "status": "success"})

                self.logger.info(
                    f"Tool executed successfully",
                    extra={
                        "tool_name": tool_name,
                        "session_id": session_id,
                        "duration_ms": round(duration_ms, 2),
                    }
                )
            else:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
                self.tool_counter.add(1, {"tool": tool_name, "status": "error"})

                self.logger.error(
                    f"Tool execution failed",
                    extra={
                        "tool_name": tool_name,
                        "session_id": session_id,
                        "error_type": exc_type.__name__,
                        "error_message": str(exc_val),
                        "duration_ms": round(duration_ms, 2),
                    }
                )

            self.tool_latency.record(duration_ms, {"tool": tool_name})
            self.span.set_attribute(LLMSemanticConventions.TOOL_DURATION_MS, duration_ms)
            self.span.end()

            return False  # Don't suppress exceptions

        def set_input(self, tool_input: Dict[str, Any]):
            """Record tool input (sanitized)."""
            # Sanitize sensitive data
            sanitized = {k: v for k, v in tool_input.items() if k not in ["password", "token", "api_key"]}
            self.span.set_attribute(LLMSemanticConventions.TOOL_INPUT, json.dumps(sanitized))

        def set_output(self, tool_output: Dict[str, Any]):
            """Record tool output summary."""
            # Only record summary to avoid large payloads
            output_summary = {
                "success": "error" not in tool_output,
                "keys": list(tool_output.keys()) if isinstance(tool_output, dict) else [],
            }
            self.span.set_attribute(LLMSemanticConventions.TOOL_OUTPUT, json.dumps(output_summary))

    return ToolTracer()


def log_conversation(
    session_id: str,
    event_type: str,
    user_email: Optional[str] = None,
    message: Optional[str] = None,
    response: Optional[str] = None,
    provider: Optional[str] = None,
    tools_used: Optional[list] = None,
    quality_score: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log conversation events for offline evaluation."""
    logger = get_logger()
    tracer = get_tracer()
    meter = get_meter()

    # Create conversation metrics
    conversation_counter = meter.create_counter(
        "conversation.events.total",
        description="Total conversation events",
        unit="1"
    )
    message_length_histogram = meter.create_histogram(
        "conversation.message.length",
        description="Length of messages",
        unit="characters"
    )

    # Build log record
    log_data = {
        "event_type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user_email": user_email,
    }

    if message:
        log_data["user_message"] = message[:500]  # Truncate for logging
        log_data["user_message_length"] = len(message)
        message_length_histogram.record(len(message), {"type": "user"})

    if response:
        log_data["agent_response"] = response[:500]  # Truncate for logging
        log_data["agent_response_length"] = len(response)
        message_length_histogram.record(len(response), {"type": "agent"})

    if provider:
        log_data["provider"] = provider

    if tools_used:
        log_data["tools_used"] = tools_used
        log_data["tool_count"] = len(tools_used)

    if quality_score is not None:
        log_data["quality_score"] = quality_score

    if metadata:
        log_data.update(metadata)

    # Record metric
    conversation_counter.add(1, {"event_type": event_type, "provider": provider or "unknown"})

    # Add trace context
    current_span = trace.get_current_span()
    if current_span.is_recording():
        span_context = current_span.get_span_context()
        log_data["trace_id"] = format(span_context.trace_id, "032x")
        log_data["span_id"] = format(span_context.span_id, "016x")

    # Log based on event type
    if event_type == "error":
        logger.error(f"Conversation event: {event_type}", extra=log_data)
    elif event_type == "warning":
        logger.warning(f"Conversation event: {event_type}", extra=log_data)
    else:
        logger.info(f"Conversation event: {event_type}", extra=log_data)

    return log_data


def create_conversation_span(session_id: str, user_email: Optional[str] = None):
    """Create a parent span for an entire conversation turn."""
    tracer = get_tracer()

    span = tracer.start_span(
        "conversation.turn",
        kind=SpanKind.SERVER
    )
    span.set_attribute(LLMSemanticConventions.CONVERSATION_ID, session_id)
    if user_email:
        span.set_attribute(LLMSemanticConventions.USER_EMAIL, user_email)

    return span


def record_fallback_event(
    session_id: str,
    from_provider: str,
    to_provider: str,
    reason: str
):
    """Record when fallback between providers occurs."""
    logger = get_logger()
    meter = get_meter()

    fallback_counter = meter.create_counter(
        "llm.fallback.total",
        description="Total number of provider fallbacks",
        unit="1"
    )

    fallback_counter.add(1, {
        "from_provider": from_provider,
        "to_provider": to_provider,
    })

    logger.warning(
        "Provider fallback occurred",
        extra={
            "session_id": session_id,
            "from_provider": from_provider,
            "to_provider": to_provider,
            "reason": reason,
        }
    )

    # Also add to current span if active
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.set_attribute(LLMSemanticConventions.FALLBACK_USED, True)
        current_span.set_attribute(LLMSemanticConventions.FALLBACK_REASON, reason)
        current_span.add_event(
            "provider_fallback",
            attributes={
                "from_provider": from_provider,
                "to_provider": to_provider,
                "reason": reason,
            }
        )
