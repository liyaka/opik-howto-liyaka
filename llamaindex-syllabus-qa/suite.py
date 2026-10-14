"""Opik test suite for the syllabus Q&A app: plain-English assertions per question."""

import opik
from opik.api_objects.dataset.execution_policy import ExecutionPolicy

SUITE_NAME = "llamaindex-syllabus-qa"

# Each item is one question plus the facts a correct answer must state.
SUITE_ITEMS = [
    {
        "question": "What is the late penalty for homework in CS 340?",
        "assertions": [
            "The answer states that homework loses 10% of its score for each day it is late",
            "The answer states that work more than five days late receives no credit",
        ],
    },
    {
        "question": "What are the grading weights in BIO 210?",
        "assertions": [
            "The answer states lab reports are 35%, the field journal 15%, the midterm 20% and the final exam 30%",
        ],
    },
    {
        "question": "When and where are Prof. Lindgren's office hours?",
        "assertions": ["The answer states Mondays from 1:00 to 3:00 pm in Vance Library, room 2B"],
    },
    {
        "question": "What are the prerequisites for CS 340?",
        "assertions": ["The answer names both CS 220 and MATH 201 as prerequisites"],
    },
    {
        "question": "When is the BIO 210 final exam?",
        "assertions": ["The answer states the final exam is on Saturday, December 12, 2026, at 1:00 pm"],
    },
    {
        "question": "Does HIST 115 have a midterm exam, and when is its final?",
        "assertions": [
            "The answer states that HIST 115 has no midterm",
            "The answer states the final exam is on Friday, December 18, 2026, from 2:00 pm to 4:00 pm",
        ],
    },
    {
        "question": "Which of the three courses lets students submit work late with no penalty at all?",
        "assertions": [
            "The answer identifies HIST 115 and its one 48-hour grace token per semester",
        ],
    },
    {
        "question": "Can I submit the BIO 210 field journal late?",
        "assertions": ["The answer states that the field journal cannot be submitted late"],
    },
]

GLOBAL_ASSERTIONS = [
    "Every number, date and room mentioned in the answer appears in the retrieved syllabus excerpts",
    "The answer names the course it is talking about",
]


def build_suite(project_name: str) -> opik.TestSuite:
    client = opik.Opik()
    # A test suite is an Opik dataset whose items carry assertions; the LLM judge checks each one.
    # Each item runs 3 times and needs 2 passes, so one flaky judge verdict does not flip the item.
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=project_name,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy=ExecutionPolicy(runs_per_item=3, pass_threshold=2),
    )
    # insert() skips items that are already in the suite, so re-running does not duplicate them.
    suite.insert([
        {"data": {"question": item["question"]}, "assertions": item["assertions"]}
        for item in SUITE_ITEMS
    ])
    return suite


def run_suite(query_engine, ask, project_name: str) -> opik.TestSuiteResult | None:
    def task(item: dict) -> dict:
        response = ask(query_engine, item["question"])
        # The excerpts travel with the answer so the judge can check the "no invented facts" assertion.
        return {
            "input": item,
            "output": {
                "answer": str(response),
                "retrieved_excerpts": [node.text for node in response.source_nodes],
            },
        }

    # run_tests sends every item through the task, has an LLM judge check the assertions
    # and records the outcome as an experiment under the suite.
    return opik.run_tests(
        test_suite=build_suite(project_name), task=task, worker_threads=3, generate_report=False,
    )


def print_result(result) -> None:
    print(f"\nPass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} items passed)")
    for item_result in result.item_results.values():
        question = item_result.test_results[0].test_case.task_output["input"]["question"]
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {question}")
        if not item_result.passed:
            for run in item_result.test_results:
                for score in run.score_results:
                    if score.scoring_failed or score.value != 1:
                        print(f"         failed: {score.name} - {score.reason}")
    if result.experiment_url:
        print(f"\nView the run: {result.experiment_url}")
