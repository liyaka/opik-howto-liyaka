"""Test suite for the voicemail triage: does the urgency call hold up?

A triage that errs toward "routine" is the dangerous direction: a poisoned dog
sits in the callback queue behind a vaccine booking. This suite feeds each
voicemail transcript through the triage step and lets an LLM judge check
assertions against the transcript and the model's answer:

  * suite-level: the callback entry is faithful to what the caller said, and
    the urgency level is justified by the pet's condition;
  * per item: the urgency level a vet receptionist would expect.

Run `uv run main.py` first to get real transcripts; without them the suite
falls back to the written scripts. Each `opik.run_tests` call becomes an
experiment in Opik.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output"

load_dotenv(EXAMPLE_DIR.parent / ".env")
os.environ.setdefault("OPIK_PROJECT_NAME", "whisper-vet-voicemail-triage")

import opik

from main import TRIAGE_MODEL, triage
from voicemails import VOICEMAILS

SUITE_NAME = "whisper-vet-voicemail-triage-suite"

GLOBAL_ASSERTIONS = [
    "The callback entry matches the transcript: the owner's name, the pet's "
    "name and the phone number are all ones the caller actually gave, and "
    "nothing is invented.",
    "The urgency level follows from what the caller says about the pet or "
    "the request (symptoms, danger, or a routine booking), not from how "
    "casual or worried the caller sounds.",
]

EXPECTED_NOTE = {
    "emergency": "possible poisoning or a life-threatening condition that needs an immediate call back",
    "same-day": "a sick or injured pet that should be seen or called today, but is not life-threatening",
    "routine": "a non-urgent request that can wait days",
}


def build_items() -> list[dict]:
    """One suite item per voicemail: the heard transcript, plus its own urgency assertion."""
    items = []
    for voicemail in VOICEMAILS:
        cached = OUTPUT_DIR / f"{voicemail['id']}.json"
        transcript = (
            json.loads(cached.read_text())["transcript"] if cached.exists() else voicemail["script"]
        )
        expected = voicemail["expected"]
        items.append(
            {
                "data": {"voicemail": voicemail["id"], "transcript": transcript},
                "assertions": [
                    f"The urgency level is '{expected}': {EXPECTED_NOTE[expected]}."
                ],
            }
        )
    return items


def task(item: dict) -> dict:
    """Triage one transcript. The judge sees this input and output."""
    return {"input": {"transcript": item["transcript"]}, "output": triage(item["transcript"])}


if __name__ == "__main__":
    # A test suite is a dataset with assertions and an execution policy: it
    # shows up under Datasets/Test suites in the project, one item per voicemail.
    client = opik.Opik()
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=os.environ["OPIK_PROJECT_NAME"],
        global_assertions=GLOBAL_ASSERTIONS,
        # Judge and triage model are both LLMs, so one run can flip. Each item
        # runs three times and must pass twice: noise is absorbed, a real
        # regression (a wrong urgency level every time) still fails.
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )

    # get_or_create returns an existing suite as-is, so assertion edits would
    # be ignored on later runs; update_test_settings pushes them as a new
    # suite version (and is a no-op when nothing changed).
    suite.update_test_settings(
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )

    existing = {item["data"]["voicemail"] for item in suite.get_items()}
    new_items = [i for i in build_items() if i["data"]["voicemail"] not in existing]
    if new_items:
        suite.insert(new_items)

    # run_tests executes task() on every item (3x each), has the judge score
    # every assertion, and records one experiment with pass/fail per item;
    # the name and config make runs comparable in the Experiments tab.
    result = opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name="triage-gpt-4o-mini",
        experiment_config={"triage_model": TRIAGE_MODEL},
    )
    print(f"\nPass rate: {result.pass_rate:.0%}")
    opik.flush_tracker()
