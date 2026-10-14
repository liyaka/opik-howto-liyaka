from typing import Any

import opik

from .agent import MODEL, extract_listing
from .corpus import GLOBAL_ASSERTIONS, ITEMS
from .tracing import PROJECT_NAME


def suite_items() -> list[dict[str, Any]]:
    """The note is the only data; expected values stay in the assertions the judge reads."""
    return [{"data": {"note": i["note"]}, "assertions": i["assertions"]} for i in ITEMS]


def run_suite(runs_per_item: int = 3, pass_threshold: int = 2):
    client = opik.Opik(project_name=PROJECT_NAME)
    # A test suite is a dataset plus assertions; it shows up under Test Suites in the project.
    # Global assertions apply to every item. The execution policy re-runs each item so one
    # unlucky LLM sample or judge call doesn't decide pass/fail.
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": runs_per_item, "pass_threshold": pass_threshold},
    )
    suite.insert(suite_items())  # deduplicated: re-running adds nothing new

    def task(item: dict[str, Any]) -> dict[str, Any]:
        return {"input": item, "output": extract_listing(item["note"])}

    # run_tests creates one experiment; an LLM judge scores every assertion per run.
    # No model override with reasoning_effort: the judge call rejects that parameter.
    result = opik.run_tests(
        test_suite=suite,
        task=task,
        experiment_name=f"listings-{MODEL.split(':')[1]}",
        worker_threads=4,
        generate_report=False,
    )
    client.flush()  # make sure the experiment items are written before the process exits
    return result
