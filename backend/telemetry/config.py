"""OpenTelemetry configuration and initialization."""
import os
import logging
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Global instances
_tracer: Optional[trace.Tracer] = None
_meter: Optional[metrics.Meter] = None
_logger: Optional[logging.Logger] = None


def init_telemetry(
    service_name: str = "bookly-support-agent",
    service_version: str = "1.0.0",
    environment: str = "development"
) -> None:
    """Initialize OpenTelemetry with OTLP exporter (via Datadog Agent)."""
    global _tracer, _meter, _logger

    # Get OTLP endpoint from environment (typically points to Datadog Agent)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "deployment.environment": environment,
        "service.namespace": "bookly",
    })

    # Set up tracing
    tracer_provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        # Export to Datadog Agent via OTLP (agent handles authentication)
        span_exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint}/v1/traces",
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        print(f"Telemetry: Exporting traces to {otlp_endpoint}")
    else:
        print("Telemetry: No exporter configured, traces will be logged locally")

    trace.set_tracer_provider(tracer_provider)
    _tracer = trace.get_tracer(service_name, service_version)

    # Set up metrics
    if otlp_endpoint:
        metric_exporter = OTLPMetricExporter(
            endpoint=f"{otlp_endpoint}/v1/metrics",
        )
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter,
            export_interval_millis=60000,  # Export every 60 seconds
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    else:
        meter_provider = MeterProvider(resource=resource)

    metrics.set_meter_provider(meter_provider)
    _meter = metrics.get_meter(service_name, service_version)

    # Set up logging with OpenTelemetry correlation
    LoggingInstrumentor().instrument(set_logging_format=True)

    # Configure structured logger
    _logger = logging.getLogger("bookly.agent")
    _logger.setLevel(logging.INFO)

    # Add handler if not already present
    if not _logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s'
        ))
        _logger.addHandler(handler)

    print(f"Telemetry initialized for {service_name} v{service_version} ({environment})")


def instrument_app(app, engine=None):
    """Instrument FastAPI app and database engine."""
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy if engine provided
    if engine:
        SQLAlchemyInstrumentor().instrument(engine=engine)

    # Instrument HTTP client (for LLM API calls)
    HTTPXClientInstrumentor().instrument()

    print("Telemetry: FastAPI, SQLAlchemy, and HTTPX instrumented")


def get_tracer() -> trace.Tracer:
    """Get the configured tracer."""
    global _tracer
    if _tracer is None:
        # Return a no-op tracer if not initialized
        return trace.get_tracer("bookly-support-agent")
    return _tracer


def get_meter() -> metrics.Meter:
    """Get the configured meter."""
    global _meter
    if _meter is None:
        return metrics.get_meter("bookly-support-agent")
    return _meter


def get_logger() -> logging.Logger:
    """Get the configured logger."""
    global _logger
    if _logger is None:
        return logging.getLogger("bookly.agent")
    return _logger
