"""The three agents: planner, researcher, writer."""

from functools import lru_cache

import opik
from langchain_openai import ChatOpenAI

from . import MODEL
from .corpus import load_corpus, search
from .state import FieldPlan, Finding, TeamState

CORPUS = load_corpus()


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0)


# type="tool" makes retrieval its own tool span under the researcher node, with the query
# and the returned sections; OpikTracer alone can drop retriever runs, so this is explicit.
@opik.track(name="retrieve_notes", type="tool")
def retrieve(query: str) -> list[dict]:
    """Look up the best-matching field-note sections for a question."""
    return search(query, CORPUS)


def planner(state: TeamState) -> dict:
    """Split the brief into focused questions."""
    plan = get_llm().with_structured_output(FieldPlan).invoke([
        ("system",
         "You lead a wildlife field-report team. The only sources are ranger notes, "
         "a sighting log summary, a waterhole and rainfall record and a patrol log "
         f"for {state['reserve']}. Break the request into 3 to 5 concrete questions "
         "that cover wildlife, water, and threats."),
        ("user", state["brief_request"]),
    ])
    return {"questions": plan.questions, "findings": []}


def researcher(state: TeamState) -> dict:
    """Answer the next unanswered question from retrieved notes."""
    question = state["questions"][len(state["findings"])]
    hits = retrieve(question)
    excerpts = "\n\n---\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    reply = get_llm().invoke([
        ("system",
         "You are a field researcher. Answer using only the excerpts below. "
         "Quote numbers and name the source file for each claim. If the excerpts "
         "do not cover it, say so plainly.\n\n" + excerpts),
        ("user", question),
    ])
    finding: Finding = {
        "question": question,
        "answer": reply.content,
        "sources": sorted({h["source"] for h in hits}),
    }
    return {"findings": state["findings"] + [finding]}


def more_questions(state: TeamState) -> str:
    """Conditional edge: loop back to the researcher until every question has a finding."""
    return "researcher" if len(state["findings"]) < len(state["questions"]) else "writer"


def writer(state: TeamState) -> dict:
    """Compose the season summary from the findings."""
    notes = "\n\n".join(
        f"### {f['question']}\n{f['answer']}\n(Sources: {', '.join(f['sources'])})"
        for f in state["findings"]
    )
    reply = get_llm().invoke([
        ("system",
         f"You write the dry-season field report for {state['reserve']}. Produce "
         "markdown: a two-sentence overview, one short section per finding, and a "
         "closing list of priorities for next season. Use only the notes below, "
         "keep numbers and source file names exact, under 400 words.\n\n" + notes),
        ("user", state["brief_request"]),
    ])
    return {"summary": reply.content}
