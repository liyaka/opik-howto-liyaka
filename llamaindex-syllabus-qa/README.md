# llamaindex-syllabus-qa

*Ask three course syllabi about grading, late work and exam dates, then watch retrieval and synthesis in Opik.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/llama--index-0.14-6a4c93?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)

Students ask the same handful of questions every semester: how much is the midterm worth, what happens if I hand it in a day late, when are office hours. Each answer sits in a different syllabus, and several syllabi use the same headings with different numbers. A RAG bot can easily answer for the wrong course. This example makes that failure visible: you can open any answer in Opik and see which excerpts were retrieved before the model wrote anything.

## What you'll build

- `syllabi.py` writes three fictional Larkspur University syllabi (CS 340 databases, BIO 210 marine ecology, HIST 115 maritime history) as PDFs. Small copies are committed in `data/`, and the app regenerates them if the folder is empty.
- `main.py` indexes them with LlamaIndex (`text-embedding-3-small`), answers five demo questions with `gpt-4o-mini`, and registers Opik's `LlamaIndexCallbackHandler` so every query becomes a trace.
- `suite.py` defines an Opik test suite: eight questions, each with plain-English assertions such as "states that homework loses 10% of its score for each day it is late", plus two suite-wide assertions. An LLM judge checks them, and each item runs 3 times and must pass 2.

## See it in Opik

Open the project **llamaindex-syllabus-qa**. The Traces tab holds 30 traces from one run: 5 `query` traces from the demo, 24 `evaluation_task` traces from the suite (8 items x 3 runs), and one `index_construction` trace.

Open a `query` trace. It contains a `retrieve` span (with an `embedding` span inside it) whose output is the syllabus chunks that matched the question, and a `synthesize` span that wraps `chunking`, `templating` and a final `llm` span. The `llm` span shows the exact prompt (the excerpts plus the question), the `gpt-4o-mini-2024-07-18` completion, around 950 prompt tokens and an estimated cost of about $0.00016. If an answer names the wrong course, `retrieve` tells you whether the right syllabus was fetched at all.

Then open **Experiments**. The run (named like `quaint_subdivision_4837` in ours) belongs to the `llamaindex-syllabus-qa` suite: 24 rows, one per item-run, with each assertion scored by the judge. In our run all 8 items passed. The retrieved excerpts are in each row's output, so a failed "no invented facts" assertion can be checked against what retrieval returned.

## Run it yourself

1. `cp .env.example .env` and add your `OPENAI_API_KEY` (or keep it in a `.env` one folder up).
2. Point the SDK at Opik: `opik configure` for Opik Cloud, or use your local `~/.opik.config`.
3. `uv sync`
4. `uv run main.py` (about 80 seconds, roughly one cent of model calls)
5. Open the `llamaindex-syllabus-qa` project in Opik.

Offline tests, no keys needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change the late penalty in `syllabi.py` to 15% per day, run `uv run syllabi.py`, and re-run: the suite fails exactly the assertions that pinned 10%.
- Set `similarity_top_k=1` in `build_query_engine` and see which questions break, such as the one that compares all three courses' late policies.
- Add a question the syllabi do not answer ("Is there a textbook?") with the assertion "The answer says the syllabus does not cover this".
- Lower `runs_per_item` to 1 and re-run a few times to see how much a single judge verdict can swing an item.

## Gotchas we hit

**The index contains text like `%PDF-1.4 ... obj << /F1 2 0 R`.** The `llama-index` meta-package no longer bundles file readers, and `SimpleDirectoryReader` silently falls back to reading a PDF as raw bytes instead of raising. Retrieval then returns junk chunks and the model says the syllabus does not cover your question. Add the reader explicitly: `llama-index-readers-file` in `pyproject.toml`.

**One flaky judge verdict flips an item to FAIL.** The judge is itself an LLM, so a borderline phrasing can fail once and pass on the next run. Give the suite an execution policy instead of re-running by hand: `ExecutionPolicy(runs_per_item=3, pass_threshold=2)` passed as `global_execution_policy` to `get_or_create_test_suite`.

**Unit tests create traces in your project even with `OPIK_TRACK_DISABLE=true`.** `LlamaIndexCallbackHandler` is registered on LlamaIndex's `Settings` at import and keeps sending `query` and `index_construction` traces regardless of that variable. Empty the handler list in a fixture (`tests/conftest.py`: `monkeypatch.setattr(Settings.callback_manager, "handlers", [])`) and call `opik.set_tracing_active(False)`.

## How it's put together

- `syllabi.py` - generates the three syllabus PDFs with reportlab.
- `main.py` - index, query engine, Opik callback handler, demo questions, entry point.
- `suite.py` - test-suite items, assertions, execution policy and the `run_tests` call.
- `data/` - the committed PDF corpus.
- `tests/test_app.py` - offline tests: PDF generation, fixture parity, suite shape, retrieval with mock models, and an `@opik.track` function run with tracking off.
- `tests/conftest.py` - detaches the Opik handler for tests so they send nothing.

---

*built with Opik · inspired by Opik's examples and documentation*
