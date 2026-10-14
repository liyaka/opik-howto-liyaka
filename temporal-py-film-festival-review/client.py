"""The client process: starts one review workflow per submission and prints the outcome."""

import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from temporalio.client import Client

load_dotenv()

from shared import TASK_QUEUE, WORKFLOW_ID_PREFIX, ReviewResult, Submission  # noqa: E402
from workflows import FestivalReviewWorkflow  # noqa: E402

DATA = Path(__file__).parent / "data" / "submissions.json"


def load_submissions(path: Path = DATA) -> list[Submission]:
    return [Submission(**row) for row in json.loads(path.read_text())]


async def review(client: Client, sub: Submission) -> ReviewResult:
    return await client.execute_workflow(
        FestivalReviewWorkflow.run,
        sub,
        id=f"{WORKFLOW_ID_PREFIX}{sub.submission_id}",
        task_queue=TASK_QUEUE,
    )


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    limit = int(os.environ.get("SUBMISSION_LIMIT", "2"))
    client = await Client.connect(address)
    for sub in load_submissions()[:limit]:
        print(f"\n=== {sub.submission_id} {sub.title}")
        result = await review(client, sub)
        print(f"genre={result.classification.genre} fit={result.classification.fit_score} "
              f"slot={result.slot.slot} (attempt {result.slot.attempt}) -> {result.decision}")
        print(result.letter)


if __name__ == "__main__":
    asyncio.run(main())
