# dspy-astronomy-fact-check

**A DSPy fact-checker, run through the same Opik test suite before and after it compiles itself: 0 of 12 claims, then 9 of 12.**

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![DSPy 3](https://img.shields.io/badge/DSPy-3.x-8B0000)
![Opik 2.2](https://img.shields.io/badge/Opik-2.2.100-2f54eb)

When an optimizer rewrites your prompt, "it got better" is only a claim until you can put the old and the new program through the same test and look at both. This example does exactly that for a small task: checking claims about a made-up star system against an offline handbook.

## What you'll build

A `dspy.ChainOfThought` program on `gpt-4o-mini` that takes a claim such as *"Maret was discovered before Tessen."* and returns two things: a verdict (`supported`, `refuted` or `not enough info`) and the id of the handbook passage that decides it (`H-08`). The reference is `data/handbook.md`, fourteen short passages about the fictional Veldara system, so the model cannot lean on what it already knows.

The signature never says what the answer should look like. The house shape (lower-case verdict label, bare passage id, `none` when the handbook is silent) only exists in twelve worked claims in `data/claims.json`. `dspy.BootstrapFewShot` mines those for four demos and compiles them into the prompt.

`main.py` then:

1. creates one Opik **test suite** of 12 held-out claims, each with an assertion that pins the right verdict and passage;
2. runs it on the uncompiled program (experiment `uncompiled`);
3. compiles with `BootstrapFewShot`, scoring the teacher's attempts with a plain Python metric (no judge tokens spent);
4. runs the **same suite** on the compiled program (experiment `compiled`).

Every DSPy call is traced by `OpikCallback`.

## See it in Opik

Open the **dspy-astronomy-fact-check** project. After one run it holds 72 traces, all named `evaluation_task`: 12 claims, 3 runs per claim (the suite's execution policy), for each of the two programs. Compilation is deliberately not traced, so none of its teacher calls are in there.

Open any trace. The tree is `task` > `ChainOfThought` > `Predict` > `LM: openai - gpt-4o-mini`, followed by the judge's own spans (`llm_judge`, a `completion` span on `gpt-5-nano`, `metrics_calculation`). The `LM` span is the one that carries token usage and cost. Its input is the whole prompt, so this is where the two programs visibly differ:

- an **uncompiled** trace sends about 790 prompt tokens, and the model answers `verdict='True'` with the evidence field holding a quoted sentence of the handbook;
- a **compiled** trace sends about 3,450 prompt tokens, because four complete worked examples now sit in the prompt, and the model answers `verdict='supported'`, `evidence='H-07'`.

Then open **Experiments** (or the **dspy-astronomy-fact-check** test suite under Datasets) and select `uncompiled` and `compiled` together. Each has 12 items on the same dataset. `uncompiled` passes 0 of 12 (0%); `compiled` passes 9 of 12 (75%). The test run's summary shows why. For `uncompiled`, both format assertions pass 0 of 36 runs: the model says `True` or `The claim is false.` and pastes the passage text where the id should be, even when it understood the claim. For `compiled`, the verdict-label assertion passes 36 of 36 and the bare-id assertion 31 of 36, and every item with a definite verdict passes. The three failures are the `not enough info` claims (0 of 9 runs): the model still answers `refuted` for claims the handbook is merely silent on, and four demos built from a twelve-claim trainset did not teach it the third label. Opik shows that per assertion, which is the useful part: compilation fixed the convention it had examples for, and the suite points at the one it did not.

Cost on the `LM` spans: about $0.0065 for the uncompiled run and $0.0116 for the compiled one (the longer prompt is what you pay for the demos). The whole run, judge included, costs roughly $0.04.

## Run it yourself

1. `cp .env.example .env` and add your `OPENAI_API_KEY` (or rely on a repo-level `.env` one directory up).
2. Point the Opik SDK at your instance: `opik configure` for Opik Cloud, or `opik configure --use_local` for a local one.
3. `uv sync`
4. `uv run main.py`
5. Open the `dspy-astronomy-fact-check` project in Opik. The run takes around ten minutes: each of the 12 claims runs three times per program and every run is judged, one worker at a time (see Gotchas).
6. Offline tests, no keys needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change `max_bootstrapped_demos` to 8 and rerun. Does the compiled program learn `not enough info`, and what does the longer prompt cost?
- Add three more `not enough info` claims to `train` in `data/claims.json` and recompile. The failing assertion in the compiled experiment is the one to watch.
- Delete the evidence rule from `check_answer` in `factcheck.py`. The optimizer will happily bootstrap demos that cite anything, and the suite's evidence assertion will say so.
- Wrap the `optimizer.compile(...)` call in `main.py` without `dspy.context(callbacks=[])` and check whether the project now holds more than the 72 suite traces: that is where the teacher's attempts would show up.

## Gotchas we hit

**Some `llm` spans have no cost.** In the trace tree the `Predict` span is typed `llm` but shows no usage and no cost. `OpikCallback` types every `Predict` that way, but the tokens are only recorded on the nested `LM: openai - gpt-4o-mini` span, which makes the parent look empty. Read cost from the `LM` spans (72 of 72 had it in our run) and treat `Predict` as a wrapper.

**One `LM` span shows no tokens and no cost.** With `run_tests(..., worker_threads=4)` one of 72 `LM` spans came back without usage. The callback reads usage from the last entry of the LM's shared call history and skips the span when that entry belongs to a different, concurrent call. Run the suite with `worker_threads=1`, as `main.py` does; all 72 spans then carried cost. The price is wall time: about 4 minutes with four workers, about 10 with one.

## How it's put together

- `factcheck.py` - the DSPy signature and program, data loaders, the exact-format check and the compile-time metric.
- `main.py` - sets up `OpikCallback`, the test suite and its execution policy, runs both experiments, compiles in between.
- `data/handbook.md` - the fictional Veldara reference, one id per passage.
- `data/claims.json` - 12 worked train claims and 12 held-out test claims, with the expected verdict and passage.
- `tests/test_factcheck.py` - offline tests: corpus integrity, answer checking, metric, suite items, and a task run with the Opik callback attached and tracking disabled.
- `tests/conftest.py` - disables Opik tracking before anything imports it.
- `pyproject.toml`, `.env.example`, `.gitignore` - uv project (Python 3.12+), key template, ignores.

*built with Opik · inspired by Opik's examples and documentation*
