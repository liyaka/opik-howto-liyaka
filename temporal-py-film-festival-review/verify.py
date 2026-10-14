"""Read the Opik project back and check that one demo run produced what the README describes."""

import os
import sys
import time

import opik

PROJECT = os.environ.get("OPIK_PROJECT_NAME", "temporal-py-film-festival-review")
EXPECTED_TRACES = int(os.environ.get("SUBMISSION_LIMIT", "2"))


def print_tree(spans, parent=None, depth=0) -> None:
    for s in sorted((s for s in spans if s.parent_span_id == parent), key=lambda s: s.start_time):
        flag = f"  ERROR: {s.error_info.message}" if s.error_info else ""
        extra = f"  [{s.type}] {s.provider}/{s.model} {s.usage} cost={s.total_estimated_cost}" if s.type == "llm" else ""
        print(f"{'  ' * depth}{s.name}{flag}{extra}")
        print_tree(spans, s.id, depth + 1)


def main() -> int:
    client = opik.Opik()
    time.sleep(2)  # let ingestion settle
    traces = client.search_traces(project_name=PROJECT, max_results=100)
    print(f"project={PROJECT} traces={len(traces)}")
    ok = len(traces) == EXPECTED_TRACES
    for t in sorted(traces, key=lambda t: t.name or ""):
        spans = client.search_spans(project_name=PROJECT, trace_id=t.id, max_results=200)
        attempts = sorted((s for s in spans if s.name == "RunActivity:check_screening_slot"), key=lambda s: s.start_time)
        llm = [s for s in spans if s.type == "llm"]
        roots = [s for s in spans if s.parent_span_id is None]
        print(f"\n{t.name}: {len(spans)} spans, {len(llm)} llm, {len(attempts)} slot attempts")
        print_tree(spans)
        if len(attempts) == 2:
            print(f"retry gap: {(attempts[1].start_time - attempts[0].start_time).total_seconds():.2f}s")
        ok &= len(attempts) == 2 and bool(attempts[0].error_info) and not attempts[1].error_info
        ok &= len(llm) == 2 and all(s.usage and s.total_estimated_cost for s in llm) and len(roots) == 1
    print("\nOK" if ok else "\nMISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
