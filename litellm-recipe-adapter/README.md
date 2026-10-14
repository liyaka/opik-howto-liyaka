# litellm-recipe-adapter

![Python](https://img.shields.io/badge/python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![LiteLLM](https://img.shields.io/badge/litellm-1.79%2B-1C7ED6?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.100-2f54eb?style=flat)

**One batch of recipe edits, two models, one cost-and-latency table you can verify in Opik.**

Choosing between a cheap OpenAI model and a cheap Anthropic model usually comes down to a gut feeling, because each SDK reports usage in its own shape and nobody wants to maintain the spreadsheet that reconciles them. Here the same six kitchen requests (make it vegan, make it gluten-free, halve or double the servings, swap out an allergen) go to `gpt-4o-mini` and `claude-haiku-4-5` through LiteLLM. The script prints a summary table, and the same numbers are already sitting in Opik, so you can check one against the other.

## What you'll build

A small recipe adapter. `data/recipes.json` holds three invented recipes (a lasagna, pancakes, a pad thai) and `data/requests.json` holds six adaptation requests against them. `main.py` runs every request against both models, one `litellm.completion` call each, and prints per-call latency, tokens and cost, then a final table: model, calls, avg latency, tokens, total cost. Two Opik pieces make it observable: LiteLLM's `OpikLogger` callback records each completion as an `llm` span with usage and estimated cost, and an `@opik.track` function around each request gives every call its own trace, tagged with the model and the kind of adaptation. `compare.py` reads the spans back from Opik and prints the same table.

## See it in Opik

Open the `litellm-recipe-adapter` project. The Traces tab has 12 rows named `adapt_recipe`, six per model, each with a tag for the model (`gpt-4o-mini` or `claude-haiku-4-5-20251001`) and one for the request kind. The cost column is filled in on every row. In my run the `gpt-4o-mini` traces cost between $0.000106 and $0.000159 each, and the Haiku ones between $0.001026 and $0.001771. Filter by a model tag and sum the column to get a per-model total; filter by the `vegan` tag instead to compare how the two models handled the same request.

Expand any trace and you see two spans: a `general` span (`adapt_recipe`) with a nested `llm` span holding the prompt, the completion, the token usage and the estimated cost. The llm span's model is recorded as the resolved name, so `gpt-4o-mini` shows up as `gpt-4o-mini-2024-07-18`. That is the cost lookup key Opik priced it with.

The printed table and the Opik side agree. From a clean run:

```
model                                  calls  avg latency  tokens   total cost
------------------------------------------------------------------------------
gpt-4o-mini                                6        2.49s    2093    $0.000809
claude-haiku-4-5-20251001                  6        2.15s    2593    $0.008033
```

`uv run compare.py` queries Opik for the `llm` spans and prints identical calls, tokens, cost and average latency (to the cent-fraction and the hundredth of a second). Haiku came out about 10x more expensive on this batch while being slightly faster; the rows are two different questions, which is why you want both columns together.

## Run it yourself

1. Make sure Opik is running locally (or `opik configure` for Cloud), then `cp .env.example .env` and add `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. The app also reads a `.env` one directory up.
2. `uv sync`
3. `uv run main.py` (about 30 seconds, under one cent in model spend)
4. `uv run compare.py` to print the same table from Opik's stored spans.
5. Open the `litellm-recipe-adapter` project in Opik and look at the Traces tab.

## Poke around

- Add a third string to `MODELS` in `recipes.py` (for example `gemini/gemini-2.0-flash`) and re-run; the table gains a row and the traces a new tag.
- Filter the Traces tab by the `allergen-swap` tag and read both models' answers side by side. Cheaper is not the same as equally careful about shellfish.
- Add "Answer in under 100 words" to the prompt in `build_prompt` and see how much of Haiku's cost premium was output length.
- Sort the Traces tab by duration instead of cost; the ranking changes.

## Gotchas we hit

- **Symptom: the llm spans show up as separate traces, not under `adapt_recipe`.** LiteLLM's callback does not know about the surrounding `@opik.track` context, so the span is orphaned. Pass it explicitly: `metadata={"opik": {"current_span_data": opik_context.get_current_span_data()}}` in the `litellm.completion` call.
- **Symptom: `RuntimeError: no running event loop` and "coroutine ... was never awaited" at startup.** `OpikLogger()` starts a periodic flush task and, in a plain script with no event loop, logs this error and falls back to sending synchronously. Traces still arrive. Quiet it by setting the `LiteLLM` logger to `CRITICAL` and filtering the `periodic_flush` `RuntimeWarning` while the logger is created, as `main.py` does.
- **Symptom: the Anthropic call goes to an unexpected host or fails when `ANTHROPIC_BASE_URL` is set in your shell.** LiteLLM honors that variable. Unset it for the run (`env -u ANTHROPIC_BASE_URL uv run main.py`) if it points at a local proxy.

## How it's put together

- `main.py` - the batch runner: `OpikLogger` callback, the `@opik.track` function `adapt_recipe`, final flush and printed table.
- `recipes.py` - loads data, builds the prompt, summarizes calls per model and formats the table (no Opik, no network).
- `compare.py` - reads llm spans back from Opik and prints the same table.
- `data/recipes.json`, `data/requests.json` - the fictional recipes and the six adaptation requests.
- `tests/test_app.py` - offline tests: data join, prompt, summary math, and `adapt_recipe` with the model stubbed and tracking disabled.

Run tests with no keys: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
