from logging import getLogger
from os import getenv
from sys import platform

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import OS_TYPE, SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from Babylon.version import VERSION

logger = getLogger(__name__)


def setup_telemetry():
    """Setup OpenTelemetry tracing."""
    if getenv("BABYLON_DISABLE_TELEMETRY", "false").lower() == "true":
        logger.info("Telemetry is disabled")
        return trace

    resource = Resource.create(
        attributes={
            SERVICE_NAME: "Babylon",
            SERVICE_VERSION: VERSION,
            OS_TYPE: platform,
        }
    )

    try:
        otlp_exporter = OTLPSpanExporter(
            endpoint=getenv(
                "OTEL_EXPORTER_OTLP_ENDPOINT", "http://telemetry.westeurope.azurecontainer.io:4318/v1/traces"
            ),
            timeout=2,
        )
        span_processor = BatchSpanProcessor(otlp_exporter, export_timeout_millis=5000)
        trace.set_tracer_provider(TracerProvider(resource=resource))
        trace.get_tracer_provider().add_span_processor(span_processor)
    except Exception as e:
        logger.warning(f"Telemetry setup failed: {e}. Continuing without telemetry.")
        trace.set_tracer_provider(TracerProvider())

    return trace
