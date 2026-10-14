"""Command line: `genre baseline`."""

import argparse

import opik

from genreclf import classify, dataset, library, prompts


def cmd_baseline(_args: argparse.Namespace) -> None:
    songs = dataset.load_songs()
    client = classify.make_client()
    accuracy, rows = classify.evaluate(client, prompts.baseline_messages(), songs)
    print(f"baseline accuracy: {accuracy:.3f} on {len(songs)} songs")
    for row in rows[:5]:
        print(f"  want {row['genre']:<10} got {row['answer'][:70]!r}")


def cmd_optimize(_args: argparse.Namespace) -> None:
    from genreclf import optimize  # imported here: opik_optimizer prints a banner on import

    optimize.run(opik.Opik())


def cmd_show_winner(_args: argparse.Namespace) -> None:
    client = opik.Opik()
    saved = library.versions(client)
    if not saved:
        print("No prompt versions saved yet. Run `genre optimize` first.")
        return
    print(f"{len(saved)} version(s) of '{saved[0].name}' in the Opik prompt library:")
    for number, version in enumerate(reversed(saved), start=1):
        print(f"  v{number}  {version.commit}  {version.metadata}")
    print("\nLatest system prompt:\n")
    print(saved[0].template[0]["content"])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="genre", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("baseline", help="score the hand-written prompt").set_defaults(func=cmd_baseline)
    sub.add_parser("optimize", help="run the optimizer and save the winner").set_defaults(func=cmd_optimize)
    sub.add_parser("show-winner", help="print the saved prompt versions").set_defaults(func=cmd_show_winner)
    args = parser.parse_args(argv)
    try:
        args.func(args)
    finally:
        # Traces are sent from a background thread; flush so none are lost on exit.
        opik.flush_tracker()
