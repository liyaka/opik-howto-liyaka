# Label Check

**`openai-shipping-label-extraction`**

*Which labels can the model really read, and which ones is it quietly guessing at?*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/openai-3.31%2B-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/Opik-2.2.100%2B-2f54eb?style=flat)

A warehouse scanner that reads a smudged, torn or crooked parcel label fails differently from one that reads a clean label, and a vision model fails differently again: it hands back a confident string either way. When the string is wrong you need the photo it was looking at, not a guess about the photo. This example extracts nine fields from fictional shipping labels with `gpt-4o-mini`, attaches every label image to its Opik trace, and runs an Opik test suite whose result is allowed to be bad news.

## What you'll build

`labels.py` draws six fictional labels with Pillow every time you run the app, so the repo carries no images. Four carriers, made-up senders and recipients, a tracking number under a barcode, a weight, a ship date. Four labels are made harder on purpose: one rotated 7 degrees, one faded with ink smudges, one with the recipient block and weight in a handwriting-style font, one with a torn patch across the end of the barcode and tracking number, and a sixth that combines rotation, fade, smudges and the tear.

`main.py` sends each image to `gpt-4o-mini` (high image detail, strict JSON schema) and gets back carrier, tracking number, service level, sender, recipient name, address and postcode, weight in kg and ship date. `track_openai` records the model call, `@opik.track` wraps the extraction, and `opik_context.update_current_trace(attachments=[...])` uploads the PNG with the trace. A test suite then holds three global format assertions and three per-label assertions containing the true values. Each label runs three times and passes if two runs pass.

## See it in Opik

Open the **`openai-shipping-label-extraction`** project. It holds 18 traces, six labels times three runs. Each trace is `evaluation_task` with `extraction_task` and `extract_label` below it, then a `chat_completion_create` llm span for `gpt-4o-mini` carrying about 25,800 prompt tokens (mostly image tiles, much of it cached across the three repeats) and a cost of roughly $0.0024. The judge's own `completion` span and its scoring spans sit in the same trace. Open any trace and its Attachments tab shows the exact PNG the model received, e.g. `everything-wrong.png`.

Then open **Test suites** and the `openai-shipping-label-extraction` suite, and its experiment `label-extraction-gpt-4o-mini`. In the committed run 4 of 6 labels pass. The clean, rotated, faded-and-smudged and handwritten labels all pass 3 of 3, which is a pleasant surprise for the handwriting. The two labels with a torn barcode area fail:

- `torn-barcode` : the true tracking number ends `-M`, which is under the tear. The model returned `KX-55208-1943` on all three runs, the visible part only, so the tracking assertion fails every time.
- `everything-wrong` : the tracking number should be `NP 1096 7742 3085`. The model returned `NP 1096 7742 3` (twice) and `NP 1096 7742 3 0` (once). It stopped at the tear instead of inventing digits, but the field is still wrong.

Judged runs vary, so your counts may differ slightly. The data was not tuned toward 100%: the failures are the point. Open the failing traces next to their attachments and you can see the model was truthful about what it saw and the label simply was not complete.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY` (or keep a `.env` one directory up). Run `opik configure` once, or set the `OPIK_*` variables, so traces reach your Opik server.
2. `uv sync`
3. `uv run main.py` (renders the labels into `out/`, extracts, runs the suite, a few minutes: 18 extractions plus judging)
4. Open the project in Opik, click a trace and open its attachment, then open the suite and the experiment link printed at the end.

Offline tests, with no keys and tracking off: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Edit `LABELS` in `labels.py` and change `left = 480` in `_tear` to `380` so the tear takes more of the number, then see whether the model starts guessing instead of truncating.
- Drop `"detail": "high"` to `"low"` in `build_messages` and compare the llm span's prompt tokens and the suite pass rate.
- Add `"fade"` to the `handwritten-recipient` effects and see where the handwriting stops being readable.
- Change `runs_per_item` and `pass_threshold` in `main.py`. Note that an existing suite keeps its original policy, so delete the suite in Opik first.

## Gotchas we hit

- **The pass rate fluctuates between runs with the same code.** A single judged run mixes extraction randomness with judge randomness. Set an execution policy on the suite, `global_execution_policy={"runs_per_item": 3, "pass_threshold": 2}`, so each item is run several times and passes on a majority.
- **A test suite does not show up under Datasets.** `get_or_create_test_suite` creates a dataset of type `evaluation_suite`; look under Test suites in the UI, and filter `rest_client.datasets.find_datasets` by name if querying from code.
- **Traces in the project are named `evaluation_task`, not `extract_label`.** `run_tests` opens its own root trace per item run. Your `@opik.track` function and the `track_openai` span are nested inside it, so search for `extract_label` among spans.

## How it's put together

- `labels.py` : ground truth for six fictional labels and the Pillow code that draws them, with rotation, fade, smudge, handwriting and tear effects.
- `main.py` : prompt and schema, the traced `extract_label`, the test suite and the run.
- `tests/test_labels.py` : offline tests for rendering, assertion building, message format, and a traced call with tracking disabled and a stubbed client.
- `tests/conftest.py` : disables Opik tracking for the test session.
- `pyproject.toml`, `.env.example`, `.gitignore` : dependencies, documented variables, and `out/` ignored.

---

*built with Opik · inspired by Opik's examples and documentation*
