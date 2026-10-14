"""The client process: starts one review workflow per submission and prints the outcome."""

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor

load_dotenv()

from shared import TASK_QUEUE, WORKFLOW_ID_PREFIX, ReviewResult, Submission  # noqa: E402
from tracing import setup_tracing  # noqa: E402
from workflows import FestivalReviewWorkflow  # noqa: E402

DATA = Path(__file__).parent / "data" / "submissions.json"


def load_submissions(path: Path = DATA) -> list[Submission]:
    return [Submission(**row) for row in json.loads(path.read_text())]


async def review(client: Client, sub: Submission) -> ReviewResult:
    # This span is the root of the Opik trace. TracingInterceptor nests StartWorkflow under it
    # and injects the trace context into the workflow headers; the worker process continues it.
    tracer = trace.get_tracer("festival-client")
    with tracer.start_as_current_span(f"review:{sub.submission_id}") as span:
        span.set_attribute("input.value", json.dumps(asdict(sub)))
        try:
            result = await client.execute_workflow(
                FestivalReviewWorkflow.run,
                sub,
                id=f"{WORKFLOW_ID_PREFIX}{sub.submission_id}",
                task_queue=TASK_QUEUE,
            )
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        span.set_attribute("output.value", json.dumps(asdict(result)))
        return result


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    limit = int(os.environ.get("SUBMISSION_LIMIT", "2"))
    provider = setup_tracing("festival-client")
    # TracingInterceptor on the client creates StartWorkflow spans and propagates the trace context.
    client = await Client.connect(address, interceptors=[TracingInterceptor()])
    for sub in load_submissions()[:limit]:
        print(f"\n=== {sub.submission_id} {sub.title}")
        result = await review(client, sub)
        print(f"genre={result.classification.genre} fit={result.classification.fit_score} "
              f"slot={result.slot.slot} (attempt {result.slot.attempt}) -> {result.decision}")
        print(result.letter)
    # Flush the client's buffered spans so the root spans reach Opik before the process exits.
    provider.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
