# optimizer-music-genre-classifier

*Let an optimizer rewrite a genre-tagging prompt, then read the whole search as a score curve in Opik.*

[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat)](pyproject.toml)
[![opik-optimizer](https://img.shields.io/badge/opik--optimizer-3.2+-orange?style=flat)](pyproject.toml)
[![setup](https://img.shields.io/badge/setup-uv-de5fe9?style=flat)](https://docs.astral.sh/uv/)

A fictional radio station wants every song in its catalogue tagged with exactly one of six genres, and the first prompt someone wrote gets about a third of them right. Not because the model cannot tell jazz from metal, but because the prompt never says how to answer, so half the replies are sentences like "The genre of the song is electronic." Rewriting it by hand means guessing. This example hands the prompt to Opik's Agent Optimizer instead, with a labelled dataset, an exact-match metric and a budget of eight candidates, and records every attempt so you can see which rewrites helped and which made things worse.

## What you'll build

A small Python package, `genreclf`, with a three-command CLI:

- `genre baseline` scores the hand-written prompt on 36 fictional song descriptions (mood, instrumentation, tempo, era hints; no real artists) and traces every call.
- `genre optimize` uploads the dataset, saves the baseline prompt to the Opik prompt library as version 1, runs a `MetaPromptOptimizer` for at most 8 trials (gpt-4o-mini does both the classifying and the reasoning), prints the score curve, and saves the winner as version 2.
- `genre show-winner` prints the saved prompt versions and the winning system prompt.

The six genres are classical, jazz, folk, metal, electronic and hip-hop, six songs each. A few are deliberate crossovers (a string quartet playing a bluesy melody, a Rhodes-piano loop over a programmed kick) so a prompt that only matches keywords stumbles. The metric is strict: the model's whole answer, lowercased and stripped of punctuation, must equal the label.

## See it in Opik

Everything lives in the project `optimizer-music-genre-classifier` at `http://localhost:5173` (or your own Opik).

**The score curve.** `genre optimize` prints a link ending in `/optimizations/<id>`; open it. The run shows nine points, one per candidate prompt, scored on all 36 songs. In the run this README was written from, the baseline scored 0.444, and the candidates came back 0.944, 0.889, 0.000, 0.694, 0.000, 0.000, 0.917 and 0.556. The three zeros are the instructive ones: those prompts asked the model to analyse the description and state the genre "clearly" without saying "one word", so the answers came back as sentences such as "The genre that best fits the description is jazz." and exact match rejected all 36. Click any trial to read its full prompt next to its per-song results.

**The traces.** Open the project's Traces tab. You will see 36 `classify_song` traces from `genre baseline`, each holding one `llm` span for gpt-4o-mini with token usage and cost, plus `evaluation_task` traces from the optimizer, one per song per candidate (324 in this run, again with `llm` spans), and three `optimization_algorithm` traces where the reasoning model drafted new prompts. In total that was 363 traces and about $0.015 of recorded model cost.

**The prompt library.** Open Prompts, filtered to the project. `music-genre-classifier` has two versions. Version 1 is the hand-written baseline; version 2 is the winner, whose metadata records `baseline_accuracy` 0.444 and `accuracy` 0.944. The winning text keeps the same six genres and adds one decisive line, "Respond with only one genre." The optimizer found no new musical knowledge, it wrote down the output contract the baseline left implicit.

Your numbers will differ. The optimizer's search is random, and a re-run can have a better or worse best trial.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have an Opik server running (or `opik configure` for Opik Cloud).
2. `cp .env.example .env` and add your `OPENAI_API_KEY` (a `.env` in a parent folder also works).
3. `uv sync`
4. `uv run genre baseline` (about 30 seconds, around a cent).
5. `uv run genre optimize` (about 90 seconds).
6. `uv run genre show-winner`, then open the optimization link printed in step 5.

## Poke around

- Open the lowest-scoring trial and read why it failed, then compare it with the winner.
- Set `MAX_TRIALS = 3` in `genreclf/config.py` and see whether a good prompt still turns up.
- Loosen `normalize` in `genreclf/metric.py` to accept "The genre is jazz." and watch how much of the baseline gap closes by itself.
- Add a seventh genre to `data/songs.json` and `GENRES`, then re-run `optimize`.

## Gotchas we hit

**The model answers "Please provide the description of the song" and every score is 0.0.** A dataset item key named `description` is reserved by Opik datasets and is silently dropped on insert, so the `{description}` placeholder in the prompt had nothing to fill; the items came back with only `genre` and `id`. Name the field anything else (here `song`) and use `{song}` in the prompt.

**Evaluation traces appear under "Default Project".** The optimizer logs a deprecation notice ("The dataset's project ('Default Project') will be used") and files its trials under the dataset's project, not the `project_name` you pass to `optimize_prompt`. Create the dataset with `client.get_or_create_dataset(name, project_name=PROJECT_NAME)`.

**`change_description` on a saved prompt comes back as `None`.** On the self-hosted server used here, `create_chat_prompt(..., change_description="...")` stores nothing that `get_chat_prompt_history` returns. `metadata=` does persist, so the scores ride there: `metadata={"baseline_accuracy": 0.444, "accuracy": 0.944}`.

**Prompts are project-scoped.** `get_chat_prompt_history(name)` without `project_name` will not find the versions saved by `genre optimize`; pass `project_name=PROJECT_NAME` on every read and write.

## How it's put together

- `genreclf/config.py` project, model, dataset and prompt names, the trial budget.
- `genreclf/dataset.py` loads and validates `data/songs.json` (36 labelled songs).
- `genreclf/metric.py` exact-match scoring used by both the baseline and the optimizer.
- `genreclf/prompts.py` the deliberately loose baseline prompt.
- `genreclf/classify.py` the traced OpenAI calls (`track_openai` plus `@opik.track`) behind `genre baseline`.
- `genreclf/optimize.py` dataset upload, the `MetaPromptOptimizer` run, the score curve and the pinned run link.
- `genreclf/library.py` saving and reading prompt versions in the Opik prompt library.
- `genreclf/report.py` turns the optimizer history into a score curve and builds the project-pinned link.
- `genreclf/cli.py` the `baseline`, `optimize` and `show-winner` commands.
- `tests/` offline tests with a stubbed OpenAI client: `OPIK_TRACK_DISABLE=true uv run pytest` (no keys needed).

---

*built with Opik · inspired by Opik's examples and documentation*
