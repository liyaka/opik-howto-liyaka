import argparse
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from .agent import extract_listing  # noqa: E402
from .corpus import ITEMS  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="listings")
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("extract", help="extract one note (text, or a 1-based corpus index)")
    one.add_argument("note", help="note text, or the number of a bundled sample note")
    args = parser.parse_args(argv)

    if args.command == "extract":
        note = args.note
        if note.isdigit():
            note = ITEMS[int(note) - 1]["note"]
        print(extract_listing(note))


if __name__ == "__main__":
    main()
