import json
from types import SimpleNamespace

import pytest

import evaluate
import main
from voicemails import VOICEMAILS


class FakeClient:
    """Stands in for the OpenAI client: canned TTS bytes, transcript and triage JSON."""

    def __init__(self, triage_json: dict):
        reply = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(triage_json)))]
        )
        self.audio = SimpleNamespace(
            speech=SimpleNamespace(create=lambda **kw: SimpleNamespace(content=b"ID3fake")),
            transcriptions=SimpleNamespace(create=lambda **kw: "Hi, this is Dana."),
        )
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: reply))


TRIAGE = {
    "urgency": "Same Day",
    "owner": "Dana",
    "pet": "Biscuit, dog",
    "number": "555-0142",
    "reason": "ate gum",
    "rationale": "possible poisoning",
}


def test_parse_triage_normalises_urgency():
    assert main.parse_triage(json.dumps(TRIAGE))["urgency"] == "same-day"


def test_parse_triage_rejects_unknown_level():
    with pytest.raises(ValueError):
        main.parse_triage('{"urgency": "whenever"}')


def test_callback_list_puts_emergencies_first():
    rows = [{"urgency": u} for u in ["routine", "emergency", "same-day", "emergency"]]
    assert [r["urgency"] for r in main.callback_list(rows)] == [
        "emergency",
        "emergency",
        "same-day",
        "routine",
    ]


def test_traced_triage_runs_with_tracking_disabled(monkeypatch):
    # triage() is an @opik.track function; with tracking disabled it behaves
    # like a plain call and returns the parsed result.
    monkeypatch.setattr(main, "get_client", lambda: FakeClient(TRIAGE))
    assert main.triage("Hi, this is Dana.")["pet"] == "Biscuit, dog"


def test_process_voicemail_writes_audio_and_record(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "get_client", lambda: FakeClient(TRIAGE))
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path)
    record = main.process_voicemail(VOICEMAILS[0])
    assert (tmp_path / f"{VOICEMAILS[0]['id']}.mp3").read_bytes() == b"ID3fake"
    assert json.loads((tmp_path / f"{VOICEMAILS[0]['id']}.json").read_text())["urgency"] == "same-day"
    assert record["transcript"] == "Hi, this is Dana."


def test_voicemails_are_short_and_labelled():
    for vm in VOICEMAILS:
        assert vm["expected"] in main.URGENCY_ORDER
        assert len(vm["script"].split()) <= 55  # about 20 seconds of speech


def test_suite_items_carry_an_urgency_assertion(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluate, "OUTPUT_DIR", tmp_path)
    items = evaluate.build_items()
    assert len(items) == len(VOICEMAILS)
    assert all(vm["expected"] in i["assertions"][0] for vm, i in zip(VOICEMAILS, items))
    assert items[0]["data"]["transcript"] == VOICEMAILS[0]["script"]
