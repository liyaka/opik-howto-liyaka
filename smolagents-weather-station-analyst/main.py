"""Ask the weather-station analyst three data-quality questions."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent / ".env")
os.environ.pop("OPENAI_BASE_URL", None)

from agent import QUESTIONS, ask, build_agent  # noqa: E402


def main() -> None:
    agent = build_agent()
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n{'=' * 72}\nQuestion {i}: {question}\n{'=' * 72}")
        print(f"\nAnswer {i}: {ask(agent, question)}")


if __name__ == "__main__":
    main()
