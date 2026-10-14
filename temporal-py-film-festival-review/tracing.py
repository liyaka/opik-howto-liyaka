"""OpenTelemetry setup shared by the client process and the worker process."""

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

PROJECT = os.environ.get("OPIK_PROJECT_NAME", "temporal-py-film-festival-review")
OTEL_ENDPOINT = os.environ.get("OPIK_OTEL_ENDPOINT", "http://localhost:5173/api/v1/private/otel")


def setup_tracing(service_name: str) -> TracerProvider:
    """Point this process's OTel spans at Opik.

    Both processes call this with the same project name, so the client's spans and the
    worker's spans are ingested into one Opik project and joined by trace id into one trace.
    """
    headers = {"Comet-Workspace": os.environ.get("OPIK_WORKSPACE", "default"), "projectName": PROJECT}
    if os.environ.get("OPIK_API_KEY"):
        headers["Authorization"] = os.environ["OPIK_API_KEY"]  # only needed for Opik Cloud
    exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT.rstrip('/')}/v1/traces", headers=headers)
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider
