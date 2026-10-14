# whisper-vet-voicemail-triage

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-3.x-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)

**A vet clinic's answering machine, triaged by a model, with the recordings one click away.**

When a voicemail is sorted wrongly, nobody can tell why: the audio is gone, the transcript might have misheard something, and the model's answer is just a label in a queue. A poisoned dog ends up behind a vaccine booking, and the only evidence is a number in a database. This example triages four fictional voicemails for the "Maple Hollow Veterinary Clinic" and keeps all of the evidence: every call is one Opik trace with the audio attached as a playable MP3, and a test suite checks the triage with an LLM judge that is run three times per item so one grumpy verdict does not fail the build.

## What you'll build

A pipeline on the OpenAI Python SDK:

1. **Speak**: `gpt-4o-mini-tts` turns each written script in `voicemails.py` into an MP3 (one voice per caller, about 13 seconds each). Nothing audio is committed; `output/` is git-ignored and rebuilt every run.
2. **Transcribe**: `gpt-4o-mini-transcribe` turns the MP3 back into text.
3. **Triage**: `gpt-4o-mini` reads the transcript and returns JSON: an urgency level (`emergency`, `same-day` or `routine`) plus a callback entry (owner, pet, number, reason).

`main.py` prints the callback list sorted most urgent first. `evaluate.py` builds an Opik test suite from the same voicemails. One of the four is deliberately tricky: the owner of a parrot says "it's probably nothing and there's no hurry" about a bird that has stopped eating, which should still be same-day.

## See it in Opik

Open the **whisper-vet-voicemail-triage** project. After `main.py` there are four traces named `triage-voicemail`, each tagged with the urgency it got (`emergency`, `same-day`, `same-day`, `routine`). Open one: the span tree is `synthesize-voicemail` (containing an `audio.speech.create` llm span with the TTS model and its cost), `transcribe` (its output is the transcript) and `triage` (containing a `chat_completion_create` llm span with `gpt-4o-mini` token counts, about 300 prompt and 80 to 90 completion tokens, and an estimated cost of roughly $0.0001).

On the trace itself, in the attachments section, is the MP3, 200 to 240 KB, playable in the browser. That is the point of the example. The transcript is what the pipeline *believes* was said; the attachment is what was said. In the verified run Whisper-family transcription turned "Lindqvist" into "Lindquist" and "Raman" into "Rahman", so the callback list carried the wrong spelling; press play and you settle it in seconds.

After `evaluate.py`, the **Experiments** tab holds one experiment, `triage-gpt-4o-mini`, on the dataset `whisper-vet-voicemail-triage-suite` (4 items, each run 3 times, so 12 runs and 12 `evaluation_task` traces in the project). The suite passed 4/4: the two suite-level assertions held on 12/12 runs, and each item's own urgency assertion held on all of its runs (`emergency` 3/3, `same-day` 6/6, `routine` 3/3).

## Run it yourself

1. `cp .env.example .env` and fill in `OPENAI_API_KEY` (or use a `.env` one directory up). Opik defaults to what is in `~/.opik.config`; for a local stack set `OPIK_URL_OVERRIDE=http://localhost:5173/api/`.
2. `uv sync`
3. `uv run main.py`: synthesizes, transcribes and triages the four voicemails and prints the callback list. A full run costs a few cents.
4. `uv run evaluate.py`: runs the test suite against the transcripts that step 3 cached in `output/` (without them it falls back to the written scripts).
5. Open the project in Opik, open a `triage-voicemail` trace and press play on the attachment.

Everything audible is synthetic: the callers, pets and 555-01xx numbers are fictional and the voices are OpenAI TTS.

## Poke around

- Change the parrot's script in `voicemails.py` to a calm "please book a checkup" and set `expected` to `routine`; check how the callback list order changes.
- Delete the sentence about birds and small animals in `TRIAGE_SYSTEM_PROMPT` in `main.py` and re-run `evaluate.py`. Watch whether the parrot item starts failing its same-day assertion.
- Set `runs_per_item` to 1 in `evaluate.py` (and in the suite via `update_test_settings`) and run a few times: you will see how often a single judge verdict flips on its own.
- Read each `transcribe` span next to its audio and look for misheard names or digits.

## Gotchas we hit

- **Symptom: you edit `GLOBAL_ASSERTIONS` and the next run still judges the old wording.** `get_or_create_test_suite` returns an existing suite as-is and ignores new assertions. Push edits with `suite.update_test_settings(global_assertions=..., global_execution_policy=...)`, which creates a new suite version only if something changed.
- **Symptom: a suite-level assertion fails 0/3 on one item and passes 3/3 on the same item in another run.** The first wording, "the urgency is justified by the pet's reported condition", does not make sense for a routine checkup: no condition is reported, so a strict judge fails it, and a lenient one let it through the first time. Word suite-level assertions so they hold for every item, and keep item-specific expectations in the item's own `assertions`. The execution policy (`runs_per_item: 3`, `pass_threshold: 2`) absorbs random flips, not a wording that is wrong.
- **Symptom: no span for the transcription, only the TTS and chat calls.** `track_openai` instruments speech synthesis and chat completions here, but not `audio.transcriptions.create`. Wrap it in your own `@opik.track(name="transcribe")` function so the transcript is recorded as a span output.
- **Symptom: the callback list has "Lindquist" for a caller who said "Lindqvist".** Speech-to-text guesses at spelling. The triage is faithful to the transcript, so the error is upstream; the attached MP3 is how you find that out.

## How it's put together

- `main.py`: the pipeline (TTS, transcription, triage, callback list) with the Opik tracing and the MP3 attachment.
- `voicemails.py`: four fictional voicemail scripts, each with a TTS voice and the urgency a receptionist would expect.
- `evaluate.py`: the Opik test suite: two suite-level assertions, one per-item urgency assertion, `runs_per_item = 3`, one experiment per run.
- `tests/test_triage.py`: offline tests with a stubbed OpenAI client (parser, ordering, a traced function with tracking disabled, the end-to-end record, the suite items).
- `tests/conftest.py`: turns tracking off and sets a dummy key so tests never touch Opik or OpenAI.

Run the tests with `uv run --group dev pytest` (or `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run --group dev pytest`).

---

*built with Opik · inspired by Opik's examples and documentation*
