# pydantic-ai-real-estate-listings

*Typed listing records from messy agent notes, and a test suite that catches the values the model made up.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-2.x-E92063?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.100-2f54eb?style=flat)

Real-estate agents jot listings down in voicemails, texts and half-sentences. A model can turn
those into a clean `PropertyListing` record, and the record always looks plausible, whether
the price came from the note or from the model's imagination. This example extracts listings
with a Pydantic AI agent, traces every call to Opik over OpenTelemetry, and runs an Opik test
suite whose plain-language assertions flag the invented values.

## What you'll build

A small package, `listings`, with a CLI. `uv run listings extract 2` extracts one note;
`uv run listings suite` runs six fictional notes through the agent three times each and has
an LLM judge check four rules for every note (nothing invented, everything derivable from
the note, a valid email, a complete record) plus two to four expectations specific to that
note ("year built is null because 2021 is the roof date").

## See it in Opik

Open the `pydantic-ai-real-estate-listings` project. Under **Traces** there are 18 traces,
one per extraction (6 notes x 3 runs). Open one: the tree is `task`, then `extract_listing`
(your function, with the note as input and the record as output), then `invoke_agent agent`,
then an `llm` span `chat gpt-4o-mini` with token counts and an estimated cost. A separate
`metrics_calculation` branch holds the judge's `llm_judge` call.

Under **Test Suites**, open `pydantic-ai-real-estate-listings` and its experiment
`listings-gpt-4o-mini`: 2 of 6 notes pass (33%). Failures from the recorded run:

- The text from Mei says "3-something hundred k?" and the agent returned `price_usd: 300000`.
- The Saltmarsh note says "new roof 2021" and the agent set `year_built: 2021`.
- The voicemail's phone number came back as the words "five five five, oh one six two".
- "DM Priya" produced `agent_name: null` on the Harlow note.

Each failing assertion carries the judge's one-sentence reason.

## Run it yourself

1. Start Opik locally, or set `OPIK_API_KEY` and `OPIK_OTLP_ENDPOINT` for a hosted workspace.
2. `cp .env.example .env` and add `OPENAI_API_KEY`.
3. `uv sync`
4. `uv run listings extract 2` for one note, then `uv run listings suite` for the suite
   (about a minute, a cent or so).

## Poke around

- Add a note of your own to `listings/corpus.py` with one or two assertions.
- Change `runs_per_item` and `pass_threshold` in `listings/suite.py` and compare experiments.
- Swap `MODEL` in `listings/agent.py` for `openai:gpt-4.1-mini` and compare pass rates.

## Gotchas we hit

**`UserError: Set the OPENAI_API_KEY environment variable` when running `pytest`.**
Pydantic AI builds the model client when the `Agent` is created, so importing the module
fails without a key. Pass `defer_model_check=True` to `Agent(...)` so the key is only
needed on the first real call; tests then use `agent.override(model=TestModel())`.

## How it's put together

- `listings/models.py` the `PropertyListing` Pydantic model.
- `listings/agent.py` the Pydantic AI agent and the traced `extract_listing`.
- `listings/corpus.py` fictional notes and their assertions.
- `listings/tracing.py` OTLP endpoint/headers, Logfire and `OpikSpanProcessor` setup, flush.
- `listings/suite.py` builds the Opik test suite and runs it.
- `listings/cli.py` the `extract` and `suite` commands.
- `tests/test_listings.py` offline tests with a stubbed model.

*built with Opik · inspired by Opik's examples and documentation*
