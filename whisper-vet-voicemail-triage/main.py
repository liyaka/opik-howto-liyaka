"""Veterinary-clinic voicemail triage.

Each fictional voicemail is spoken by TTS, transcribed, then triaged by a
small model into an urgency level plus a callback entry.
"""

import functools
import json
from pathlib import Path

from dotenv import load_dotenv

EXAMPLE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXAMPLE_DIR / "output"

load_dotenv(EXAMPLE_DIR.parent / ".env")

from openai import OpenAI

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
    return OpenAI()


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


def process_voicemail(voicemail: dict) -> dict:
    """One voicemail end to end: audio -> transcript -> triage."""
    audio_path = OUTPUT_DIR / f"{voicemail['id']}.mp3"
    synthesize_voicemail(voicemail, audio_path)
    transcript = transcribe(audio_path)
    result = triage(transcript)
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
