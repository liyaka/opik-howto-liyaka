from typing import Any

import opik
from pydantic_ai import Agent

from .models import PropertyListing
from .tracing import PROJECT_NAME

MODEL = "openai:gpt-4o-mini"

agent = Agent(
    MODEL,
    output_type=PropertyListing,
    defer_model_check=True,
    system_prompt=(
        "You turn messy real-estate agent notes, voicemail transcripts and texts "
        "into a property listing record. Fill in only what the note says. If a "
        "field is not stated, leave it null; never guess or invent values."
    ),
)


# @opik.track opens the root span of the trace (named extract_listing, with the note as input
# and the record as output); the Pydantic AI spans nest inside it.
@opik.track(project_name=PROJECT_NAME)
def extract_listing(note: str) -> dict[str, Any]:
    """One extraction: messy note in, typed listing out (as a plain dict)."""
    result = agent.run_sync(note)
    return result.output.model_dump()
