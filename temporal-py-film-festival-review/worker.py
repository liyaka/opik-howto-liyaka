"""The worker process: runs the workflow and the activities."""

import asyncio
import os

from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.worker import Worker

load_dotenv()

from activities import check_screening_slot, classify_submission, draft_letter  # noqa: E402
from shared import TASK_QUEUE  # noqa: E402
from workflows import FestivalReviewWorkflow  # noqa: E402


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[FestivalReviewWorkflow],
        activities=[classify_submission, check_screening_slot, draft_letter],
    )
    print(f"WORKER_READY {address} queue={TASK_QUEUE}", flush=True)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
