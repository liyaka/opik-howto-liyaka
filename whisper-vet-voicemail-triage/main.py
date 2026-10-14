"""Veterinary-clinic voicemail triage.

Each fictional voicemail is spoken by TTS, transcribed, then triaged by a
small model into an urgency level plus a callback entry.
"""

import functools
import json
import os
from pathlib import Path

from dotenv import load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output"

load_dotenv(EXAMPLE_DIR.parent / ".env")
# Pin the Opik project before opik is imported: every trace of this app
# lands in the "whisper-vet-voicemail-triage" project instead of "Default".
os.environ.setdefault("OPIK_PROJECT_NAME", "whisper-vet-voicemail-triage")

import opik
from openai import OpenAI
from opik import Attachment, opik_context
from opik.integrations.openai import track_openai

from voicemails import VOICEMAILS

TTS_MODEL = "gpt-4o-mini-tts"
TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
TRIAGE_MODEL = "gpt-4o-mini"

URGENCY_ORDER = ["emergency", "same-day", "routine"]

TRIAGE_SYSTEM_PROMPT = """\
You triage voicemails left on a veterinary clinic's phone line. The text you
receive is an automatic transcript of the call. Reply with JSON only, in
exactly this shape:

{
  "urgency": "emergency" | "same-day" | "routine",
  "owner": "the caller's name as spoken",
  "pet": "the pet's name, and species if stated",
  "number": "the callback number, digits and dashes only",
  "reason": "one short sentence on why they called",
  "rationale": "one short sentence on why you chose this urgency"
}

Urgency rules:
- emergency: possible poisoning, trouble breathing, collapse, severe
  bleeding, seizures, or anything life-threatening. Call back immediately.
- same-day: pain, injury, or a pet that has stopped eating or drinking, even
  when the caller says it is probably nothing. Birds and small animals hide
  illness, so treat quiet behaviour as a warning sign.
- routine: checkups, vaccines, refills and other things that can wait days.
Judge the pet's condition, not the caller's tone.
"""


@functools.cache
def get_client() -> OpenAI:
    # track_openai wraps the client: the TTS and chat calls become llm child
    # spans with token usage and cost. Transcription is not instrumented, so
    # the @opik.track "transcribe" span below is what records it.
    return track_openai(OpenAI())


# @opik.track opens a span named "synthesize-voicemail" under the current
# trace, with the arguments as input and the returned byte size as output.
@opik.track(name="synthesize-voicemail")
def synthesize_voicemail(voicemail: dict, audio_path: Path) -> int:
    """Speak the script with TTS and save it as MP3. Returns the byte size."""
    response = get_client().audio.speech.create(
        model=TTS_MODEL,
        voice=voicemail["voice"],
        input=voicemail["script"],
        response_format="mp3",
    )
    audio_path.write_bytes(response.content)
    return len(response.content)


# The span's output is the transcript, so a mis-heard name shows up right
# next to the audio attached to the parent trace.
@opik.track(name="transcribe")
def transcribe(audio_path: Path) -> str:
    """Speech-to-text. Returns the plain transcript."""
    with audio_path.open("rb") as audio_file:
        return get_client().audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=audio_file,
            response_format="text",
        )


def parse_triage(raw: str) -> dict:
    """Parse the model's JSON and normalise the urgency label."""
    data = json.loads(raw)
    urgency = str(data.get("urgency", "")).strip().lower().replace(" ", "-")
    if urgency not in URGENCY_ORDER:
        raise ValueError(f"unknown urgency {data.get('urgency')!r}")
    data["urgency"] = urgency
    return data


# Wraps the chat call so the triage span holds the transcript in and the
# parsed urgency/callback entry out; the llm span nests inside it.
@opik.track(name="triage")
def triage(transcript: str) -> dict:
    """Transcript -> urgency level and callback entry."""
    response = get_client().chat.completions.create(
        model=TRIAGE_MODEL,
        messages=[
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
    )
    return parse_triage(response.choices[0].message.content)


def callback_list(results: list[dict]) -> list[dict]:
    """Callback entries, most urgent first (stable within a level)."""
    return sorted(results, key=lambda r: URGENCY_ORDER.index(r["urgency"]))


# Top-level function: one call = one trace per voicemail, with the whole
# pipeline as its span tree.
@opik.track(name="triage-voicemail")
def process_voicemail(voicemail: dict) -> dict:
    """One voicemail end to end: audio -> transcript -> triage."""
    audio_path = OUTPUT_DIR / f"{voicemail['id']}.mp3"
    synthesize_voicemail(voicemail, audio_path)
    transcript = transcribe(audio_path)
    result = triage(transcript)
    # Attach the MP3 the pipeline heard: Opik uploads it and shows a player on
    # the trace. The urgency tag makes traces filterable by outcome.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(audio_path), content_type="audio/mpeg")],
        tags=[result["urgency"]],
        metadata={"voicemail_id": voicemail["id"], "caller": voicemail["caller"]},
    )
    record = {"id": voicemail["id"], "transcript": transcript, **result}
    (OUTPUT_DIR / f"{voicemail['id']}.json").write_text(json.dumps(record, indent=2))
    return record


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    results = []
    for voicemail in VOICEMAILS:
        record = process_voicemail(voicemail)
        results.append(record)
        print(f"[{record['urgency']:<9}] {voicemail['id']}: {record['transcript']}")

    print("\nCallback list (most urgent first)")
    for r in callback_list(results):
        print(f"  {r['urgency']:<9} {r['owner']} / {r['pet']} / {r['number']} / {r['reason']}")

    # Traces and attachments are sent from a background thread; flush so the
    # process doesn't exit before they reach Opik.
    opik.flush_tracker()
    print("\nDone. Open the whisper-vet-voicemail-triage project in Opik.")
