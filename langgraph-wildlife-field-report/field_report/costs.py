"""Per-agent token and cost roll-up, computed from the spans Opik stored for a trace."""

import time
from collections import defaultdict

import opik

from . import PROJECT_NAME

AGENTS = ("planner", "researcher", "writer")


def agent_of(span, by_id: dict) -> str | None:
    """Name of the top-level node span (planner/researcher/writer) that contains `span`."""
    while span.parent_span_id and span.parent_span_id in by_id:
        span = by_id[span.parent_span_id]
    return span.name if span.name in AGENTS else None


def per_agent(spans: list) -> dict[str, dict]:
    """Sum tokens, cost and pass count per agent from llm spans."""
    by_id = {s.id: s for s in spans}
    rows: dict[str, dict] = {a: {"passes": 0, "tokens": 0, "cost": 0.0} for a in AGENTS}
    for s in spans:
        if s.parent_span_id is None and s.name in rows:
            rows[s.name]["passes"] += 1
        if s.type == "llm" and (agent := agent_of(s, by_id)):
            rows[agent]["tokens"] += (s.usage or {}).get("total_tokens") or 0
            rows[agent]["cost"] += s.total_estimated_cost or 0.0
    return rows


def fetch_spans(trace_id: str, expected_llm_spans: int = 1, wait: float = 15.0) -> list:
    """Read the trace's spans back from Opik; ingestion is async, so poll briefly."""
    client = opik.Opik(project_name=PROJECT_NAME)
    deadline = time.time() + wait
    while True:
        spans = client.search_spans(project_name=PROJECT_NAME, trace_id=trace_id, max_results=500)
        llm = [s for s in spans if s.type == "llm" and s.total_estimated_cost is not None]
        if len(llm) >= expected_llm_spans or time.time() > deadline:
            return spans
        time.sleep(1)


def format_table(rows: dict[str, dict]) -> str:
    lines = [f"{'agent':<12}{'passes':>7}{'tokens':>9}{'cost (USD)':>13}"]
    for name, r in rows.items():
        lines.append(f"{name:<12}{r['passes']:>7}{r['tokens']:>9}{r['cost']:>13.6f}")
    total_tokens = sum(r["tokens"] for r in rows.values())
    total_cost = sum(r["cost"] for r in rows.values())
    lines.append(f"{'total':<12}{'':>7}{total_tokens:>9}{total_cost:>13.6f}")
    return "\n".join(lines)
