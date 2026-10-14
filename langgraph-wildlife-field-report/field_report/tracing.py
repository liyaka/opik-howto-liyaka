"""Opik tracing for the graph."""

import opik
from opik.integrations.langchain import OpikTracer, track_langgraph

from . import PROJECT_NAME
from .graph import build_graph


def build_traced_graph():
    """Compile the graph and attach Opik tracing to it."""
    # OpikTracer turns each graph run into ONE trace: a span per node pass, the model
    # calls nested as llm spans with tokens and cost. Everything lands in PROJECT_NAME.
    tracer = OpikTracer(project_name=PROJECT_NAME, tags=["field-report"])
    # track_langgraph attaches the tracer to the compiled graph and records its
    # structure on the trace, which is what the agent-graph view renders.
    return track_langgraph(build_graph(), tracer)


def flush() -> None:
    # Traces are sent from a background thread; flush so a short-lived CLI doesn't exit first.
    opik.flush_tracker()
