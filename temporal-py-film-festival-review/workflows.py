"""The durable review workflow: classify, check a slot (with retries), draft the letter."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import check_screening_slot, classify_submission, decide, draft_letter
    from shared import ReviewResult, Submission


@workflow.defn
class FestivalReviewWorkflow:
    @workflow.run
    async def run(self, sub: Submission) -> ReviewResult:
        classification = await workflow.execute_activity(
            classify_submission, sub, start_to_close_timeout=timedelta(seconds=60)
        )
        slot = await workflow.execute_activity(
            check_screening_slot,
            args=[sub.submission_id, classification.genre],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(initial_interval=timedelta(seconds=1), maximum_attempts=4),
        )
        decision = decide(classification, slot)
        letter = await workflow.execute_activity(
            draft_letter,
            args=[sub, classification, slot, decision],
            start_to_close_timeout=timedelta(seconds=60),
        )
        return ReviewResult(sub.submission_id, classification, slot, decision, letter)
