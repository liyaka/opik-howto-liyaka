# temporal-py-film-festival-review

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![Temporal](https://img.shields.io/badge/temporalio-1.34-000000)
![Opik](https://img.shields.io/badge/Opik-OTLP-2f54eb)

**One review, two operating-system processes, one Opik trace, with the failed first attempt still on the record.**

A film festival wants every short-film submission to be reviewed by a durable workflow: a model classifies the film, a scheduling service is asked whether a screening slot is free, and a model drafts the decision letter. Temporal makes that survive crashes and flaky services. The cost is that no single process sees the whole run: one process starts the workflow, another executes it. This example shows how to get that run back as a single trace in Opik, including the retried call that failed before it succeeded.

## What you'll build

A `FestivalReviewWorkflow` (Temporal Python SDK) with three activities:

1. `classify_submission` asks `gpt-4o-mini` for a genre and a 1-10 fit score.
2. `check_screening_slot` looks up an open slot for that genre. It is deliberately flaky: attempt 1 always raises `Screening scheduler unavailable (503)`, and the retry policy (1 s initial interval) makes attempt 2 succeed.
3. `draft_letter` asks `gpt-4o-mini` for the decision letter (accepted, waitlisted or declined).

`demo.py` starts the dev server that ships inside the `temporalio` package (no Temporal CLI, no Docker), launches `worker.py` as one subprocess and `client.py` as another, and shuts everything down. Both subprocesses install `temporalio.contrib.opentelemetry.TracingInterceptor` and export OTLP spans to the same Opik project; the LLM calls add `gen_ai.*` span attributes so Opik reads model, token usage and cost.

## See it in Opik

Open the `temporal-py-film-festival-review` project. A default run produces **2 traces**, `review:SUB-2101` and `review:SUB-2102`, each with **13 spans**. Open one and expand the tree:

- `review:SUB-2101` (client process) wraps `StartWorkflow:FestivalReviewWorkflow`. Everything below it was created in the worker process: `RunWorkflow`, `CompleteWorkflow`, and a `StartActivity:` / `RunActivity:` pair per activity.
- Under `StartActivity:check_screening_slot` there are **two** `RunActivity:check_screening_slot` spans. The first carries the error `Screening scheduler unavailable (503)`; the second is clean and starts about 1.0 s later.
- `RunActivity:classify_submission` and `RunActivity:draft_letter` each contain a `chat gpt-4o-mini` span of type `llm`, provider `openai`, with prompt and completion. In the verified run SUB-2101 used 119 prompt + 48 completion tokens for the classifier and 96 + 76 for the letter, about $0.0001 for the whole trace.

Temporal's own UI says the workflow completed; this view also says what the model said at each step, what it cost, and that the scheduling service was down on first contact.

## Run it yourself

1. `cd temporal-py-film-festival-review && cp .env.example .env` and set `OPENAI_API_KEY`.
2. Start Opik locally (or set `OPIK_OTEL_ENDPOINT` and `OPIK_API_KEY` for Opik Cloud). Defaults assume `http://localhost:5173/api/v1/private/otel`, workspace `default`.
3. `uv run python demo.py` (about 13 s; set `TEMPORAL_PORT` if 7233 is taken, `SUBMISSION_LIMIT=3` for all three films).
4. `uv run --with opik python verify.py` reads the project back, prints the span tree and exits non-zero if the retry, the llm spans or their cost are missing.
5. Offline tests: `OPIK_TRACK_DISABLE=true uv run pytest`.

To run the two roles by hand against your own Temporal server: `uv run python worker.py` in one terminal, `uv run python client.py` in another (`TEMPORAL_ADDRESS` selects the server).

## Poke around

- In `activities.py` change `attempt == 1` to `attempt <= 3`: three red `RunActivity` spans, then a green one. With `maximum_attempts=4` in `workflows.py` that is the last chance; use `<= 4` to see the workflow fail and the client span turn red.
- Raise the 1 s `initial_interval` and read the longer gap straight off the two attempt spans.
- Edit a logline in `data/submissions.json` to be a poor fit and watch `decide()` produce a "waitlisted" or "declined" letter, with the reasoning in the classify span.
- Set `SUBMISSION_LIMIT=3` to include the 21-minute horror submission and compare its classify span with the other two.

## Gotchas we hit

**The trace is missing its last spans (10 spans instead of 13, one llm span instead of two).** The worker was stopped with SIGTERM (`worker.terminate()`), which kills Python before the `BatchSpanProcessor` flushes. Stop it with SIGINT (`worker.send_signal(signal.SIGINT)`) and call `provider.shutdown()` in a `finally`, as `worker.py` and `demo.py` do. The client needs the same `provider.shutdown()` before it exits.

**`llm` spans show token usage but `total_estimated_cost` is `None` and provider is `None`.** Raw OTLP spans have no provider, so Opik cannot price them. Set `span.set_attribute("gen_ai.system", "openai")` next to the model and usage attributes (see `llm.py`); cost then appears per span.

## How it's put together

- `demo.py` dev server, worker subprocess, client subprocess, graceful shutdown.
- `worker.py` worker process with `TracingInterceptor` and span flush.
- `client.py` client process: root `review:<id>` span, workflow start, printing.
- `workflows.py` the durable workflow and its retry policy.
- `activities.py` the three activities, flaky slot check and the `decide()` rule.
- `llm.py` OpenAI call wrapped in a `gen_ai.*` span, plus the classifier parser.
- `tracing.py` OTLP exporter pointed at Opik, shared by both processes.
- `shared.py` dataclasses and task queue name.
- `data/submissions.json` three fictional submissions.
- `verify.py` reads the Opik project back and checks the trace shape.
- `tests/test_app.py` offline tests: parser, decision rule, flaky activity, `gen_ai` attributes, exporter config.

---

*built with Opik · inspired by Opik's examples and documentation*
