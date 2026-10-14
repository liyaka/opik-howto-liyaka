"""Types and constants shared by the client, the worker and the workflow."""

from dataclasses import dataclass

TASK_QUEUE = "film-festival-review"
WORKFLOW_ID_PREFIX = "review-"


@dataclass
class Submission:
    submission_id: str
    title: str
    director: str
    email: str
    runtime_min: int
    logline: str


@dataclass
class Classification:
    genre: str
    fit_score: int
    rationale: str


@dataclass
class SlotOffer:
    submission_id: str
    available: bool
    slot: str | None
    attempt: int


@dataclass
class ReviewResult:
    submission_id: str
    classification: Classification
    slot: SlotOffer
    decision: str
    letter: str
