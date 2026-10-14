import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .tracing import flush_tracing, setup_tracing  # noqa: E402

setup_tracing()

from .agent import extract_listing  # noqa: E402
from .corpus import resolve_note  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="listings")
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("extract", help="extract one note (text, or a 1-based corpus index)")
    one.add_argument("note", help="note text, or the number of a bundled sample note")
    sub.add_parser("suite", help="run the Opik test suite over the bundled notes")
    args = parser.parse_args(argv)

    if args.command == "extract":
        print(extract_listing(resolve_note(args.note)))
    else:
        from .suite import run_suite

        result = run_suite()
        print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items)")
        for item_result in result.item_results.values():
            note = item_result.test_results[0].test_case.task_output["input"]["note"]
            print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {note[:60]!r}")
        print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")
    flush_tracing()


if __name__ == "__main__":
    main()
