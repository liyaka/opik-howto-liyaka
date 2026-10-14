import os

PROJECT_NAME = "pydantic-ai-real-estate-listings"


def setup_tracing() -> None:
    """Send Pydantic AI's OpenTelemetry spans to Opik. Call once, before the first agent run."""
    # The OTLP endpoint + headers tell Opik which workspace and project receive the spans;
    # without projectName they land in "Default Project".
    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
    endpoint = os.getenv("OPIK_OTLP_ENDPOINT", "http://localhost:5173/api/v1/private/otel")
    headers = [f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')}", f"projectName={PROJECT_NAME}"]
    if os.getenv("OPIK_API_KEY"):  # Opik Cloud only; local Opik takes no Authorization header
        headers.insert(0, f"Authorization={os.environ['OPIK_API_KEY']}")
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = ",".join(headers)
    os.environ["OTEL_METRICS_EXPORTER"] = "none"

    import logfire
    from opik.integrations.otel import OpikSpanProcessor

    # OpikSpanProcessor attaches the agent's spans to the surrounding @opik.track trace,
    # so each extraction is ONE trace instead of a trace plus a detached OTel one.
    logfire.configure(send_to_logfire=False, additional_span_processors=[OpikSpanProcessor()])
    # Emits invoke_agent / chat <model> spans (with token usage) for every Pydantic AI run.
    logfire.instrument_pydantic_ai()


def flush_tracing() -> None:
    import logfire
    import opik

    # Both exporters batch in the background; without these the process can exit with spans unsent.
    logfire.force_flush()
    opik.flush_tracker()
