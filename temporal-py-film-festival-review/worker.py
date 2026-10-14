"""The worker process: runs the workflow and the activities."""

import asyncio
import os

from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

load_dotenv()

from activities import check_screening_slot, classify_submission, draft_letter  # noqa: E402
from shared import TASK_QUEUE  # noqa: E402
from tracing import setup_tracing  # noqa: E402
from workflows import FestivalReviewWorkflow  # noqa: E402


async def main() -> None:
    # Spans created in this process (activities, workflow, LLM calls) go to Opik.
    provider = setup_tracing("festival-worker")
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    # TracingInterceptor on the worker side reads the trace context the client put in the
    # workflow headers, so RunWorkflow / RunActivity spans (one per attempt, errors included)
    # become children of the client's span instead of starting a new trace.
    client = await Client.connect(address, interceptors=[TracingInterceptor()])
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[FestivalReviewWorkflow],
        activities=[classify_submission, check_screening_slot, draft_letter],
    )
    print(f"WORKER_READY {address} queue={TASK_QUEUE}", flush=True)
    try:
        await worker.run()
    finally:
        # Flush buffered spans: without this the last spans never reach Opik when the worker stops.
        provider.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # SIGINT from the demo launcher: the finally block in main() already flushed spans
