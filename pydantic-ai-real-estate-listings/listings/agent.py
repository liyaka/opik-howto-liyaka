from typing import Any

from pydantic_ai import Agent

from .models import PropertyListing

MODEL = "openai:gpt-4o-mini"

agent = Agent(
    MODEL,
    output_type=PropertyListing,
    system_prompt=(
        "You turn messy real-estate agent notes, voicemail transcripts and texts "
        "into a property listing record. Fill in only what the note says. If a "
        "field is not stated, leave it null; never guess or invent values."
    ),
)


def extract_listing(note: str) -> dict[str, Any]:
    """One extraction: messy note in, typed listing out (as a plain dict)."""
    result = agent.run_sync(note)
    return result.output.model_dump()
