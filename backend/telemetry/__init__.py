"""OpenTelemetry configuration for Bookly support agent."""
from .config import init_telemetry, get_tracer, get_logger, get_meter, is_telemetry_enabled
from .agent_instrumentation import (
    trace_llm_call,
    trace_tool_execution,
    log_conversation,
    record_fallback_event,
    create_conversation_span,
)

__all__ = [
    "init_telemetry",
    "get_tracer",
    "get_logger",
    "get_meter",
    "is_telemetry_enabled",
    "trace_llm_call",
    "trace_tool_execution",
    "log_conversation",
    "record_fallback_event",
    "create_conversation_span",
]
