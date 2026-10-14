"""Send smolagents spans to a local Opik over OpenTelemetry."""

import os

PROJECT_NAME = "smolagents-weather-station-analyst"
# Local Opik's OTLP ingestion path; the exporter appends /v1/traces itself.
OPIK_OTEL_ENDPOINT = "http://localhost:5173/api/v1/private/otel"


def setup_tracing():
    if os.getenv("OPIK_TRACK_DISABLE", "").lower() == "true":
        return None  # same switch the Opik SDK honours: nothing is exported
    # Comet-Workspace picks the workspace and projectName picks the Opik project
    # the traces land in; a local install needs no Authorization header.
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", OPIK_OTEL_ENDPOINT)
    os.environ.setdefault(
        "OTEL_EXPORTER_OTLP_HEADERS",
        f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')},projectName={PROJECT_NAME}",
    )

    from openinference.instrumentation.smolagents import SmolagentsInstrumentor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    # SimpleSpanProcessor exports each span as it ends, so a crashed run still leaves a partial trace.
    provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
    # The instrumentor patches smolagents: each agent.run becomes a trace, each step and each
    # model call (generated code) a child span, with execution logs on the step span.
    SmolagentsInstrumentor().instrument(tracer_provider=provider)
    return provider
