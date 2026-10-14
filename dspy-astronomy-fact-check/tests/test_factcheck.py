import dspy
import pytest
from dspy.utils.dummies import DummyLM

import factcheck
import main
from opik.integrations.dspy.callback import OpikCallback


def test_handbook_has_every_cited_passage():
    handbook = factcheck.load_handbook()
    for split in ("train", "test"):
        for row in factcheck.load_claims(split):
            if row["passage"] != "none":
                assert f"[{row['passage']}]" in handbook


def test_splits_are_disjoint_and_cover_all_verdicts():
    train = {r["claim"] for r in factcheck.load_claims("train")}
    test = factcheck.load_claims("test")
    assert not train & {r["claim"] for r in test}
    assert {r["verdict"] for r in test} == set(factcheck.VERDICTS)


@pytest.mark.parametrize(
    "verdict, evidence, ok",
    [
        ("supported", "H-07", True),
        ("The claim is true.", "H-07", False),
        ("supported", "[H-07] Orrin's largest moon", False),
        ("supported", "H-08", False),
        ("not enough info", "none", True),
        ("not enough info", "H-06", False),
    ],
)
def test_check_answer(verdict, evidence, ok):
    expected_verdict = "not enough info" if evidence == "none" or verdict == "not enough info" else "supported"
    expected_passage = "none" if expected_verdict == "not enough info" else "H-07"
    assert factcheck.check_answer(verdict, evidence, expected_verdict, expected_passage) is ok


def test_metric_reads_prediction_fields():
    example = factcheck.to_examples(factcheck.load_claims("train")[:1])[0]
    good = dspy.Prediction(verdict=example.verdict, evidence=example.evidence)
    bad = dspy.Prediction(verdict="refuted", evidence=example.evidence)
    assert factcheck.metric(example, good)
    assert not factcheck.metric(example, bad)


def test_suite_items_pin_the_expected_answer():
    items = main.suite_items(factcheck.load_claims("test"))
    assert len(items) == 12
    refuted = next(i for i in items if i["data"]["claim"] == "Maret was discovered before Tessen.")
    assert refuted["assertions"] == ["The verdict is 'refuted' and the evidence is H-08"]
    nei = next(i for i in items if "debris disk" in i["data"]["claim"])
    assert "'not enough info'" in nei["assertions"][0] and "'none'" in nei["assertions"][0]


def test_task_with_opik_callback_and_tracking_disabled():
    # The OpikCallback is attached exactly as in main.py; with OPIK_TRACK_DISABLE
    # set (see conftest.py) it records nothing and does not change the result.
    lm = DummyLM([{"reasoning": "H-07 says so", "verdict": "supported", "evidence": "H-07"}])
    callback = OpikCallback(project_name=main.PROJECT_NAME)
    with dspy.context(lm=lm, callbacks=[callback]):
        task = main.make_task(factcheck.build_program())
        out = task({"claim": "Piper is about 3,900 km in diameter."})
    assert out == {
        "input": {"claim": "Piper is about 3,900 km in diameter."},
        "output": {"verdict": "supported", "evidence": "H-07"},
    }
