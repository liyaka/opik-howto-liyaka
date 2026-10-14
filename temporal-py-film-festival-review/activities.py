"""The three activities: two LLM calls around a deliberately flaky scheduling lookup."""

from temporalio import activity
from temporalio.exceptions import ApplicationError

from llm import chat, parse_classification
from shared import Classification, SlotOffer, Submission

# Fictional festival programme: genre -> the next open screening slot.
SCREENING_SLOTS = {
    "documentary": "Fri 18:30, Harbour Hall",
    "comedy": "Sat 20:00, Main Screen",
    "horror": "Sat 23:15, Cellar Cinema",
    "drama": "Sun 15:00, Main Screen",
}

CLASSIFY_SYSTEM = (
    "You screen short films for a small international festival. Reply with JSON: "
    '{"genre": one of documentary|comedy|horror|drama, "fit_score": integer 1-10 for '
    'how well it fits a programme of intimate, character-led shorts, "rationale": one sentence}.'
)

LETTER_SYSTEM = (
    "You write warm, concise decision letters (max 110 words) for a short-film festival. "
    "Sign off as 'The Programming Team'. Never promise anything beyond what the facts say."
)


@activity.defn
async def classify_submission(sub: Submission) -> Classification:
    raw = await chat(
        CLASSIFY_SYSTEM,
        f"Title: {sub.title}\nRuntime: {sub.runtime_min} min\nLogline: {sub.logline}",
        json_mode=True,
    )
    return Classification(**parse_classification(raw))


@activity.defn
async def check_screening_slot(submission_id: str, genre: str) -> SlotOffer:
    """Stands in for a flaky scheduling service: the first attempt always fails."""
    attempt = activity.info().attempt
    if attempt == 1:
        raise ApplicationError("Screening scheduler unavailable (503)")
    slot = SCREENING_SLOTS.get(genre)
    return SlotOffer(submission_id=submission_id, available=slot is not None, slot=slot, attempt=attempt)


@activity.defn
async def draft_letter(sub: Submission, classification: Classification, slot: SlotOffer, decision: str) -> str:
    facts = {
        "title": sub.title,
        "director": sub.director,
        "decision": decision,
        "genre": classification.genre,
        "screening_slot": slot.slot,
    }
    return await chat(LETTER_SYSTEM, f"Facts: {facts}")


def decide(classification: Classification, slot: SlotOffer) -> str:
    """Accept when the film fits the programme and there is a slot for its genre."""
    if classification.fit_score >= 7 and slot.available:
        return "accepted"
    if classification.fit_score >= 5:
        return "waitlisted"
    return "declined"


