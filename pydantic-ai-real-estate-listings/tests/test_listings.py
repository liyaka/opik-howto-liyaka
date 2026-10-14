import os

os.environ["OPIK_TRACK_DISABLE"] = "true"

from pydantic_ai.models.test import TestModel

from listings.agent import agent, extract_listing
from listings.corpus import GLOBAL_ASSERTIONS, ITEMS, resolve_note
from listings.models import PropertyListing
from listings.suite import suite_items


def test_traced_function_runs_with_tracking_disabled():
    model = TestModel(custom_output_args={"address": "1 Test St", "bedrooms": 2})
    with agent.override(model=model):
        record = extract_listing("2bd at 1 Test St")
    assert record["address"] == "1 Test St"
    assert record["price_usd"] is None


def test_only_address_is_required():
    assert PropertyListing(address="5 Elm").bathrooms is None


def test_resolve_note_by_index_and_literal():
    assert resolve_note("1") == ITEMS[0]["note"]
    assert resolve_note("hello 3bd") == "hello 3bd"


def test_suite_items_keep_answers_out_of_data():
    items = suite_items()
    assert len(items) == len(ITEMS)
    for item in items:
        assert set(item["data"]) == {"note"}
        assert item["assertions"]


def test_corpus_has_global_rules_and_a_null_check():
    assert any("invented" in a for a in GLOBAL_ASSERTIONS)
    assert any("null" in a for i in ITEMS for a in i["assertions"])
