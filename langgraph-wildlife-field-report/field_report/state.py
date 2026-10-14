"""The shared state that flows through the graph."""

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Finding(TypedDict):
    question: str
    answer: str
    sources: list[str]


class TeamState(TypedDict, total=False):
    reserve: str
    brief_request: str
    questions: list[str]
    findings: list[Finding]
    summary: str


class FieldPlan(BaseModel):
    """The planner's structured output."""

    questions: list[str] = Field(
        description="3 to 5 focused questions the field notes can answer for the season summary"
    )
