"""Run one Opik test suite on the uncompiled fact-checker and on the compiled one.

DSPy calls are traced with OpikCallback. The suite is shared: the same twelve
held-out claims and the same assertions are run against both programs, so the
two experiments in Opik differ only in the program that answered.
"""

import os
import pathlib

PROJECT_NAME = "dspy-astronomy-fact-check"
SUITE_NAME = "dspy-astronomy-fact-check"
# Read by the Opik SDK: the suite, its experiments and the run_tests traces all
# land in this project instead of "Default Project".
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import dotenv
import dspy
import opik
from opik.integrations.dspy.callback import OpikCallback

import factcheck

dotenv.load_dotenv(pathlib.Path(__file__).parents[1] / ".env")

MODEL = "openai/gpt-4o-mini"

# Plain-language quality bar, checked by Opik's LLM judge for every item.
GLOBAL_ASSERTIONS = [
    "The verdict is exactly one of the three lower-case labels 'supported', "
    "'refuted' or 'not enough info', with no other words around it",
    "The evidence is only a bare passage id such as 'H-07', or the word 'none', "
    "with no quoted text and no brackets",
]

ITEM_ASSERTION = {
    "supported": "The verdict is 'supported' and the evidence is {passage}",
    "refuted": "The verdict is 'refuted' and the evidence is {passage}",
    "not enough info": "The verdict is 'not enough info' and the evidence is 'none'",
}


def suite_items(rows: list[dict]) -> list[dict]:
    """One suite item per held-out claim; the item's assertion pins the right answer."""
    return [
        {
            "data": {"claim": r["claim"]},
            "assertions": [ITEM_ASSERTION[r["verdict"]].format(passage=r["passage"])],
        }
        for r in rows
    ]


def make_task(program: dspy.Module):
    handbook = factcheck.load_handbook()

    def task(item: dict) -> dict:
        # The OpikCallback spans (module, predict, LM) nest under the trace that
        # run_tests opens for this item, so each run is one inspectable tree.
        pred = program(handbook=handbook, claim=item["claim"])
        return {
            "input": {"claim": item["claim"]},
            "output": {"verdict": pred.verdict, "evidence": pred.evidence},
        }

    return task


def run_suite(suite, program: dspy.Module, name: str, config: dict):
    # run_tests runs every item through the program, lets the judge score the
    # assertions, and records one experiment named `name` on the suite's dataset.
    return opik.run_tests(
        test_suite=suite,
        task=make_task(program),
        experiment_name=name,
        experiment_config={"model": MODEL, "program": "ChainOfThought(FactCheck)", **config},
        # One worker: OpikCallback reads token usage from the LM's shared history,
        # and concurrent calls can overwrite each other's entry (the span then has
        # no usage and no cost).
        worker_threads=1,
        generate_report=False,
    )


def main() -> None:
    # OpikCallback turns every DSPy module, predictor and LM call into spans
    # (llm spans carry tokens and cost); log_graph=True also stores the module graph.
    dspy.configure(
        lm=dspy.LM(MODEL, cache=False),
        callbacks=[OpikCallback(project_name=PROJECT_NAME, log_graph=True)],
    )

    client = opik.Opik()
    # A test suite is a dataset plus assertions and an execution policy. Each item
    # runs 3 times and must pass 2: the judge and the model are both LLMs, so a
    # single run can flip, while a consistently wrong answer still fails.
    policy = {"runs_per_item": 3, "pass_threshold": 2}
    suite = client.get_or_create_test_suite(
        name=SUITE_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy=policy,
    )
    suite.update_test_settings(global_assertions=GLOBAL_ASSERTIONS, global_execution_policy=policy)
    test_rows = factcheck.load_claims("test")
    if not suite.get_items():
        suite.insert(suite_items(test_rows))

    uncompiled = factcheck.build_program()
    print("Running the suite on the uncompiled program...")
    before = run_suite(suite, uncompiled, "uncompiled", {"compiled": False})

    # Compilation fires dozens of teacher calls. They are not the thing under
    # test, so tracing is switched off for this block; otherwise they would
    # sit in the project next to the suite traces.
    print("\nCompiling with BootstrapFewShot (not traced)...")
    optimizer = dspy.BootstrapFewShot(
        metric=factcheck.metric, max_bootstrapped_demos=4, max_labeled_demos=4, max_rounds=1
    )
    with dspy.context(callbacks=[]):
        compiled = optimizer.compile(
            uncompiled, trainset=factcheck.to_examples(factcheck.load_claims("train"))
        )

    print("\nRunning the same suite on the compiled program...")
    after = run_suite(
        suite,
        compiled,
        "compiled",
        {"compiled": True, "optimizer": "BootstrapFewShot", "demos": len(compiled.predict.demos)},
    )

    print("\n=== Same suite, two experiments ===")
    for label, result in (("uncompiled", before), ("compiled  ", after)):
        print(f"{label}: {result.items_passed}/{result.items_total} items passed ({result.pass_rate:.0%})")
    if after.experiment_url:
        print(f"\nView the runs: {after.experiment_url}")
    # Traces and experiment rows are sent from background threads; without a flush
    # the last ones can be lost when the script exits.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
