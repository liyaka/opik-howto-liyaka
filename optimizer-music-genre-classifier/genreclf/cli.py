"""Command line: `genre baseline`."""

import argparse

import opik

from genreclf import classify, dataset, prompts


def cmd_baseline(_args: argparse.Namespace) -> None:
    songs = dataset.load_songs()
    client = classify.make_client()
    accuracy, rows = classify.evaluate(client, prompts.baseline_messages(), songs)
    print(f"baseline accuracy: {accuracy:.3f} on {len(songs)} songs")
    for row in rows[:5]:
        print(f"  want {row['genre']:<10} got {row['answer'][:70]!r}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="genre", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline", help="score the hand-written prompt").set_defaults(func=cmd_baseline)
    args = parser.parse_args(argv)
    try:
        args.func(args)
    finally:
        # Traces are sent from a background thread; flush so none are lost on exit.
        opik.flush_tracker()
