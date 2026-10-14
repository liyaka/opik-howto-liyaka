# anthropic-ts-boardgame-rules-qa

*A rules referee that has to show its sources, and a test suite that checks every quote it shows.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Anthropic SDK](https://img.shields.io/badge/%40anthropic--ai%2Fsdk-0.133-191919?style=flat)
![Opik](https://img.shields.io/badge/opik%20(npm)-2.2.100-2f54eb?style=flat)

Ask a chatbot a rules question mid-game and you get a confident ruling. Ask it again after the argument
starts and you want to know where in the rulebook that came from. An answer that cannot point at the
text is an answer somebody has to take on faith, and a model happily invents a "house rule" that sounds
right. This example makes the model cite, then makes a test suite verify the citations, so a prompt
or model change that starts producing fake quotes shows up as a red row instead of a lost game night.

## What you'll build

A small TypeScript program around **Lanternfall**, a made-up night-market board game whose rulebook lives
in `data/rulebook.md`. Claude Haiku 4.5, called through the plain Anthropic TS SDK, answers six rules
questions and must wrap every ruling's support in `<quote>...</quote>` tags copied from the rulebook.

The quality bar is written in plain English and stored in an Opik **test suite**:

- *Global assertions* (checked on every answer): every `<quote>` appears verbatim in the rulebook, the quotes support the ruling, the answer addresses the question.
- *Item-level assertions* on two questions that have exactly one right ruling: Wick tokens cannot be traded, and the tie-break order (most unspent Wick tokens, then shared victory).
- *Execution policy*: each question is run 3 times and must pass 2 of them, so one unlucky judge verdict does not fail a good answer.

There is no first-party Opik integration for the Anthropic TypeScript SDK, so the Claude call is traced by
hand: one `llm` span carrying the model, provider `anthropic` and token usage.

## See it in Opik

Open the **`anthropic-ts-boardgame-rules-qa`** project. The Traces tab holds 18 traces named
`evaluation_task`: 6 questions times 3 runs each. Open one and the tree reads `llm_task` >
`answer_question` > `anthropic.messages.create`, followed by the scoring spans `metrics_calculation` >
`llm_judge` > `model.generateText`. The `anthropic.messages.create` span is of type `llm`, shows
`claude-haiku-4-5-20251001` under provider `anthropic`, around 1,850 prompt tokens (the whole
rulebook rides along in the system prompt) and a few hundred completion tokens, and an estimated cost of
about $0.003. The answer text with its `<quote>` blocks is in the span's output.

Then open **Test suites** and pick **`lanternfall-citation-checks`**. The newest run shows 6 of 6
items passed (pass rate 100%), each item with 3 of 3 runs passing. Click an item to see every
assertion with the judge's reason and a link to the trace that produced the answer. The Wick-token item lists four assertions, the tie-break item five, and the other four items the three global ones.

A pass rate of 100% is the healthy baseline. The suite earns its keep on the day it drops.

## Run it yourself

1. `cd anthropic-ts-boardgame-rules-qa && npm install`
2. `cp .env.example .env` and set `ANTHROPIC_API_KEY` (a `.env` one directory up also works).
3. Point the SDK at your Opik: `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default` (for Opik Cloud set `OPIK_API_KEY` and `OPIK_WORKSPACE` instead).
4. `npm run demo` (if your shell has `ANTHROPIC_BASE_URL` set to a gateway, run `env -u ANTHROPIC_BASE_URL npm run demo`; see Gotchas)
5. Open the project and the test suite named above. The run takes about 35 seconds and costs a few cents.

Offline tests (no keys, tracking off): `OPIK_TRACK_DISABLE=true npm test`. `OPIK_TRACK_DISABLE=true` is
the TypeScript SDK's switch that turns `track()` into a plain pass-through.

## Poke around

- Add a failing assertion: append `"The response contains no <quote> tags"` to `GLOBAL_ASSERTIONS` in `src/suite.ts`. Delete the suite (or change its name) so the new bar is applied, re-run, and every item fails with the judge's reason.
- Ask something the rulebook never covers ("Can I steal a card from someone's hand?") by adding a question plus an assertion such as "The response says the rulebook does not cover this".
- Weaken the prompt: remove "copied character for character" from `buildSystemPrompt` in `src/qa.ts`, re-run, and compare the two experiments.
- Change `runsPerItem` / `passThreshold` in `buildSuite` to see how the policy decides an item's verdict.

## Gotchas we hit

**Every judge verdict says `LLM scoring failed: Failed to generate provider response with model claude-haiku-4-5`**,
so every item fails 0/3, while the app's own calls work. The judge runs through `@ai-sdk/anthropic`, which
reads `ANTHROPIC_BASE_URL` too but treats it as the full API prefix (its default is
`https://api.anthropic.com/v1` and it appends `/messages`). `@anthropic-ai/sdk` appends `/v1` itself, so a
gateway URL without `/v1` that works for the app returns "Not Found" for the judge. Unset it for the run:

```sh
env -u ANTHROPIC_BASE_URL npm run demo
```

**The `answer_question` span shows up as type `llm`** with no model or usage. `track()` without a `type`
defaults to `llm`. Give wrapper functions `type: OpikSpanType.General` and keep `llm` for the span that
carries the model and usage.

**Traces never arrive, or only the suite's arrive.** `track()` uses its own global client, separate from
the `new Opik()` you built the suite with. Call `await flushAll()` (not `opik.flush()`) before exiting.

## How it's put together

- `data/rulebook.md`: the fictional Lanternfall rulebook the model answers from.
- `src/qa.ts`: system prompt, model constant and the `answerQuestion` function (takes any client with `messages.create`).
- `src/quotes.ts`: pulls `<quote>` blocks out of an answer and checks them against the rulebook text locally.
- `src/questions.ts`: the six rules questions.
- `src/tracing.ts`: the manual `llm` span (model, provider, usage) and the general `answer_question` span.
- `src/suite.ts`: the test suite with global and item-level assertions, execution policy, and the `runTests` call.
- `src/main.ts`: loads env, runs the suite, prints per-item pass/fail, flushes.
- `tests/quotes.test.ts`, `tests/qa.test.ts`: offline vitest tests with a stubbed client, including a traced call with tracking disabled.
- `vitest.config.ts`: turns tracking off for the tests.

---

*built with Opik · inspired by Opik's examples and documentation*
