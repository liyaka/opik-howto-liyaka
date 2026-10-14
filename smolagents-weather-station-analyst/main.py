"""Ask the weather-station analyst three data-quality questions."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent / ".env")
os.environ.pop("OPENAI_BASE_URL", None)

from tracing import PROJECT_NAME, setup_tracing  # noqa: E402

# Must run before the agent is built so smolagents is already instrumented.
provider = setup_tracing()

from agent import QUESTIONS, ask, build_agent  # noqa: E402
from checks import ground_truth, load_readings  # noqa: E402


def main() -> None:
    agent = build_agent()
    truth = ground_truth(load_readings())
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n{'=' * 72}\nQuestion {i}: {question}\n{'=' * 72}")
        print(f"\nAnswer {i}: {ask(agent, question)}")
        print(f"Ground truth {i}: {truth[i - 1]}")

    # shutdown flushes any spans still queued in the exporter before the process exits.
    if provider:
        provider.shutdown()
    print(f"\nDone. Open the '{PROJECT_NAME}' project in Opik: one trace per question.")


if __name__ == "__main__":
    main()
