"""Command-line entry point: `uv run field-report`."""

import argparse

from dotenv import load_dotenv

from .tracing import build_traced_graph, flush

DEFAULT_REQUEST = (
    "Write the 2025 dry-season field report for Kestrel Hollow Reserve: "
    "wildlife trends, water stress, and anti-poaching results."
)


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Generate a season field report")
    parser.add_argument("--request", default=DEFAULT_REQUEST, help="what the report should cover")
    parser.add_argument("--reserve", default="Kestrel Hollow Reserve")
    args = parser.parse_args(argv)

    result = build_traced_graph().invoke({"reserve": args.reserve, "brief_request": args.request})

    print("Planner questions:")
    for i, q in enumerate(result["questions"], 1):
        print(f"  {i}. {q}")
    print(f"\n{result['summary']}")
    flush()


if __name__ == "__main__":
    main()
