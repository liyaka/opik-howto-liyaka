"""Command-line entry point: `uv run field-report`."""

import argparse

from dotenv import load_dotenv

from .costs import fetch_spans, format_table, per_agent
from .tracing import build_traced_graph, flush

DEFAULT_REQUEST = (
    "Write the 2025 dry-season field report for Kestrel Hollow Reserve: "
    "wildlife trends, water stress, and anti-poaching results."
)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate a season field report")
    parser.add_argument("--request", default=DEFAULT_REQUEST, help="what the report should cover")
    parser.add_argument("--no-costs", action="store_true", help="skip the per-agent cost table")
    parser.add_argument("--reserve", default="Kestrel Hollow Reserve")
    args = parser.parse_args(argv)

    app, tracer = build_traced_graph()
    result = app.invoke({"reserve": args.reserve, "brief_request": args.request})

    print("Planner questions:")
    for i, q in enumerate(result["questions"], 1):
        print(f"  {i}. {q}")
    print(f"\n{result['summary']}")
    flush()
    if not args.no_costs:
        # Read the trace back from Opik: llm spans carry usage and total_estimated_cost,
        # and grouping them under their node span gives tokens and dollars per agent.
        trace_id = tracer.created_traces()[0].id
        spans = fetch_spans(trace_id, expected_llm_spans=len(result["questions"]) + 2)
        print("\nPer-agent cost, read back from Opik:\n" + format_table(per_agent(spans)))
        print(f"\nTrace id: {trace_id}")


if __name__ == "__main__":
    main()
