# opik-ts-podcast-title-prompts

*Write the episode-title prompt once, version it in Opik, and let a test suite tell you which version is better: 0 of 6 episodes pass on v1, 6 of 6 on v2.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![opik](https://img.shields.io/badge/opik-2.2.100-2f54eb?style=flat)

A title prompt is the kind of text people tweak in a hurry: "make it catchier", "shorter please". Each tweak ships without a record of what the old wording was, and nobody can say whether the new one is actually better. Here the prompt for a made-up podcast, *The Slow Lantern*, lives in Opik's prompt library, every edit is a new immutable version, and one test suite grades both versions on the same six episodes so the difference is a number, not an impression.

## What you'll build

- A title generator on `gpt-4o-mini` (OpenAI Node SDK) for six fictional episode summaries in `data/episodes.json`.
- A prompt called `episode-title` in the Opik prompt library with two versions: v1 asks for "a catchy, attention-grabbing title", v2 adds three bullet rules (7 words max; plain text with no colons, quotes, emoji or hashtags; a concrete subject taken from the summary, no hype words).
- Tracing with the Opik TypeScript SDK: each generation is a `generate_title` span around an `llm` span with model, provider, usage and cost, and the prompt version it used is attached to the trace.
- An Opik test suite, `episode-title-checks`, with four plain-English assertions graded by an LLM judge (three runs per item, two must pass). It runs once per prompt version, producing two experiments.

## See it in Opik

Open the `opik-ts-podcast-title-prompts` project, then the **Prompts** page (the prompt library) and click `episode-title`. It has two versions, v1 and v2. Open the version history and compare them: the diff shows the three bullet rules v2 added around v1's one-line instruction. Neither version can be edited; a change would be v3.

Back in the project, open the **Experiments** tab (or the `episode-title-checks` test suite). There are two runs, `episode-title-v1` and `episode-title-v2`, each over the same 6 items, 18 judged runs apiece. v1 passes 0 of 6 items (0%) and v2 passes 6 of 6 (100%). Each experiment is linked to its prompt version. What v1 does wrong is consistent: every v1 title wraps itself in quotation marks and most have a colon ("Midnight Whispers: Night-Shift Tales from the Coastal Frontlines"), and they run long. Across the 18 judged runs, 0 pass the 7-word assertion and only 1 passes the plain-text assertion. The hype-word and on-topic assertions mostly pass for v1 (17 of 18 each), so the jump comes from format, not from topic drift. v2 gives titles like "The Clock That Ran Four Minutes Slow" and passes the word-count, plain-text and hype-word assertions in all 18 runs, and the on-topic one in 17.

Open the **Traces** tab. There are 37 traces: 36 `evaluation_task` traces from the suite and one `generate_title` trace from the single sample generation in the demo. Expand a trace: a `generate_title` span (type `general`) holds an `openai.chat.completions.create` span (type `llm`, model `gpt-4o-mini-2024-07-18`, provider `openai`) with token usage and an estimated cost (about $0.00003 for the sample). The trace metadata carries the prompt name, version and commit, so you can tell which wording produced a title.

One run's numbers are one run's numbers: the judge is an LLM, so the borderline item (the listener-mailbag episode) passed v2 in only 2 of 3 runs here, which is still a pass under the 2-of-3 policy. If you re-run and an item flips, that is the policy doing its job, not a bug.

## Run it yourself

1. `cd opik-ts-podcast-title-prompts && npm install`
2. `cp .env.example .env` and put your `OPENAI_API_KEY` in it (a `.env` one or two directories up is also read). Point `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` at your Opik (the example uses a local self-hosted server; for Opik Cloud also set `OPIK_API_KEY`).
3. `npm run demo`. It takes about one to two minutes and costs a few cents.
4. Open the project in Opik as described above.

Offline tests (no keys, tracking off): `OPIK_TRACK_DISABLE=true npm test`. That variable is the TypeScript SDK's switch that makes `track()` a plain pass-through. Type check with `npm run typecheck`.

## Poke around

- Add a fifth assertion to `GLOBAL_ASSERTIONS` in `src/suite.ts`, for example "The title does not repeat the guest's name", delete the `episode-title-checks` suite in Opik (or rename it) and re-run to see which version breaks it.
- Write a v3 in `src/prompts.ts` (say, require the title to be a question) and call `createPrompt` for it; the library gains v3, and you can add a third `runSuiteForVersion` call.
- Soften v2 by dropping the 7-word rule and watch the per-assertion tally printed by the demo to see which rule carried the pass rate.
- Change `runsPerItem` / `passThreshold` in `buildSuite` to 1 / 1 and see how much the verdict on the mailbag episode depends on judge noise.

## Gotchas we hit

**`Error inserting items into dataset: ... Cannot deserialize value of type java.util.UUID from String "ep-01"`.** An item's data field called `id` is read as the dataset item's own id, which must be a UUID. Name your key something else (this example uses `slug`): `suite.insert([{ data: { slug: "ep-01", summary } }])`.

**Re-running creates a v3 that is a copy of v1.** `createPrompt` only compares against the latest version, so after v2 exists, passing v1's text again is "different" and adds a version. Look the version up first and only create it when it is missing:

```ts
const existing = await client.getPrompt({ name, version: "v1", projectName });
if (!existing) await client.createPrompt({ name, prompt: text, projectName });
```

**Cost is empty on the span.** `opik-openai` logs its completions with span type `general` (hardcoded in 2.2.100), and Opik only prices `llm` spans. This example wraps the call in `track({ type: OpikSpanType.Llm, enrichSpan })` and returns `model`, `provider: "openai"` and `usage` from `enrichSpan`; with that the span shows tokens and cost.

**`AI SDK Warning: System messages in the prompt or messages fields...` printed once per judged run.** It comes from the LLM judge inside the Opik SDK, not from this app, and is harmless. It does not affect the results.

## How it's put together

- `data/episodes.json`: the six fictional episode summaries.
- `src/episodes.ts`: loads the episodes.
- `src/titles.ts`: model constant, message building and `generateTitle` for any client with `chat.completions.create`.
- `src/prompts.ts`: the two prompt versions and the idempotent `registerPromptVersions` that writes them to the prompt library.
- `src/tracing.ts`: the `llm` span with usage and cost, and `makeTitleGenerator`, which fetches a prompt version and traces the call.
- `src/suite.ts`: the test suite, its assertions and execution policy, and `runSuiteForVersion` (one experiment per version).
- `src/main.ts`: registers prompts, makes one sample generation, runs the suite for v1 and v2, prints the comparison, flushes.
- `tests/titles.test.ts`: offline vitest tests with a stubbed client, including a traced call with tracking disabled.
- `vitest.config.ts`: turns tracking off for the tests.

---

*built with Opik · inspired by Opik's examples and documentation*
