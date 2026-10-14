"""A DSPy fact-checker for claims about the fictional Veldara star system.

Given a claim, the program reads the handbook in data/handbook.md and
returns a verdict (supported / refuted / not enough info) plus the passage
id that decides it. The house answer shape is never spelled out in the
signature: it lives in the worked examples in data/claims.json.
"""

import json
import pathlib
import re

import dspy

DATA = pathlib.Path(__file__).parent / "data"
VERDICTS = ("supported", "refuted", "not enough info")
PASSAGE_ID = re.compile(r"^(H-\d{2}|none)$")


def load_handbook() -> str:
    return (DATA / "handbook.md").read_text()


def load_claims(split: str) -> list[dict]:
    return json.loads((DATA / "claims.json").read_text())[split]


class FactCheck(dspy.Signature):
    """Fact-check the claim against the handbook."""

    handbook: str = dspy.InputField(desc="the Veldara system handbook")
    claim: str = dspy.InputField()
    verdict: str = dspy.OutputField()
    evidence: str = dspy.OutputField(desc="the passage that decides the claim")


def build_program() -> dspy.Module:
    return dspy.ChainOfThought(FactCheck)


def to_examples(rows: list[dict]) -> list[dspy.Example]:
    return [
        dspy.Example(
            handbook=load_handbook(),
            claim=r["claim"],
            verdict=r["verdict"],
            evidence=r["passage"],
        ).with_inputs("handbook", "claim")
        for r in rows
    ]


def check_answer(verdict: str, evidence: str, expected_verdict: str, expected_passage: str) -> bool:
    """Exact house format: lower-case verdict label, bare passage id (or 'none')."""
    verdict, evidence = verdict.strip(), evidence.strip()
    return (
        verdict == expected_verdict
        and PASSAGE_ID.match(evidence) is not None
        and evidence == expected_passage
    )


def metric(example: dspy.Example, prediction, trace=None) -> bool:
    """Compile-time metric: purely programmatic, so compiling spends no judge tokens."""
    return check_answer(prediction.verdict, prediction.evidence, example.verdict, example.evidence)
