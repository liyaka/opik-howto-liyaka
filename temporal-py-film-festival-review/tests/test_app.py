import dataclasses
import json
from types import SimpleNamespace

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from temporalio.exceptions import ApplicationError
from temporalio.testing import ActivityEnvironment

import llm
from activities import check_screening_slot, decide
from client import load_submissions
from shared import Classification, SlotOffer


def test_submissions_load():
    subs = load_submissions()
    assert len(subs) >= 2 and all(s.submission_id.startswith("SUB-") for s in subs)


def test_parse_classification_clamps_and_normalises():
    out = llm.parse_classification('{"genre": " Drama ", "fit_score": 42, "rationale": "ok"}')
    assert out == {"genre": "drama", "fit_score": 10, "rationale": "ok"}


@pytest.mark.parametrize(
    "score,available,expected",
    [(9, True, "accepted"), (9, False, "waitlisted"), (5, True, "waitlisted"), (3, True, "declined")],
)
def test_decide(score, available, expected):
    slot = SlotOffer("SUB-1", available, "Fri" if available else None, 2)
    assert decide(Classification("drama", score, ""), slot) == expected


async def test_slot_check_fails_first_attempt_then_succeeds():
    with pytest.raises(ApplicationError, match="503"):
        await ActivityEnvironment().run(check_screening_slot, "SUB-1", "drama")
    env = ActivityEnvironment()
    env.info = dataclasses.replace(env.info, attempt=2)
    offer = await env.run(check_screening_slot, "SUB-1", "drama")
    assert offer.available and offer.attempt == 2


async def test_chat_records_gen_ai_attributes_with_tracking_disabled(monkeypatch):
    # Runs with OPIK_TRACK_DISABLE=true and no keys: the OTel span code does not need either.
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(llm, "tracer", provider.get_tracer("test"))

    async def fake_create(**kwargs):
        return SimpleNamespace(
            model="gpt-4o-mini-test",
            choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=5),
        )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))
    monkeypatch.setattr(llm, "AsyncOpenAI", lambda: fake_client)

    assert await llm.chat("sys", "user") == "hello"
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["gen_ai.system"] == "openai"
    assert attrs["gen_ai.usage.input_tokens"] == 11 and attrs["gen_ai.usage.output_tokens"] == 5
    assert json.loads(attrs["gen_ai.prompt"])[1]["content"] == "user"


def test_setup_tracing_targets_project(monkeypatch):
    import tracing

    seen = {}
    monkeypatch.setattr(tracing, "OTLPSpanExporter", lambda **kw: seen.update(kw) or InMemorySpanExporter())
    monkeypatch.setenv("OPIK_WORKSPACE", "default")
    tracing.setup_tracing("test-service")
    assert seen["headers"]["projectName"] == "temporal-py-film-festival-review"
    assert seen["endpoint"].endswith("/api/v1/private/otel/v1/traces")
