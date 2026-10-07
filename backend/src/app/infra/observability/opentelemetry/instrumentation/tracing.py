from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter

from app.presentation.api.config.models import OpentelemetryConfig


def setup_tracing(config: OpentelemetryConfig) -> TracerProvider:
    resource = Resource.create({SERVICE_NAME: config.service_name})
    tracer_provider = TracerProvider(resource=resource)

    exporter: SpanExporter
    if config.traces_exporter != "none":
        if config.traces_exporter == "otlp":
            exporter = OTLPSpanExporter(
                endpoint=config.exporter_otlp_endpoint,
                insecure=True,
            )
        elif config.traces_exporter == "console":
            exporter = ConsoleSpanExporter()
        else:
            msg = f"Unknown traces_exporter: {config.traces_exporter}"
            raise ValueError(msg)

        tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(tracer_provider)
    return tracer_provider
