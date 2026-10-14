"""Print the same per-model table from what Opik stored, to check it against main.py's output."""

import os

import opik
from dotenv import load_dotenv
from pathlib import Path

from recipes import Call, format_table, summarize

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
PROJECT = "litellm-recipe-adapter"


def main() -> None:
    # search_spans reads back the llm spans that OpikLogger wrote; their model, usage and
    # total_estimated_cost fields are the same numbers the Opik traces table sums per trace.
    client = opik.Opik(project_name=PROJECT)
    client.flush()
    spans = client.search_spans(project_name=PROJECT, filter_string='type = "llm"', max_results=1000)
    calls = []
    for s in spans:
        calls.append(Call(
            model=f"{s.provider}/{s.model}",
            latency_s=(s.end_time - s.start_time).total_seconds(),
            tokens=(s.usage or {}).get("total_tokens", 0),
            cost_usd=s.total_estimated_cost or 0.0,
        ))
    print(f"{len(calls)} llm spans in project {PROJECT}\n")
    print(format_table(summarize(calls)))


if __name__ == "__main__":
    main()
