<div align="center">

# openai-ts-museum-visitor-desk

*A museum front-desk chatbot whose chats show up in Opik as chats, with a price tag on every reply.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-6.x-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.2.100-2f54eb?style=flat)

</div>

A visitor asks whether the museum is open on Thursday night, then how much a family ticket costs, then what the kids can do. Three questions, one conversation. In a plain request log, that is three unrelated API calls, and you cannot tell which visitor asked what, what a whole chat cost, or whether the visitor left happy.

This example is a small chatbot for the (made-up) Harrowgate Museum of Tides and Tools. It answers opening-hours, ticket, exhibit and accessibility questions from a fact sheet, remembers earlier turns, and reports everything to Opik so that conversations, costs and a satisfaction score are all queryable.

## What you'll build

- `VisitorDesk`: one object per conversation, holding the message history and calling the OpenAI Node SDK (`gpt-4o-mini`) directly, with no framework.
- A trace per turn, all sharing the conversation's `threadId`, each containing one hand-logged `llm` span with model, provider and token usage.
- Two scripted conversations (`thursday-evening-family`, `wheelchair-visit`), three turns each, so the demo needs no typing.
- A `visitor-satisfaction` feedback score written onto an existing trace after the run, the way a thumbs-up button would.
- `npm run verify`, which reads the project back from Opik and prints what is there.

## See it in Opik

Open the **openai-ts-museum-visitor-desk** project.

- **Threads tab**: two threads, `thursday-evening-family` and `wheelchair-visit`, with three turns each. Opening one reads like a chat transcript: the visitor's question, the desk's answer, repeat.
- **Traces tab**: six traces named `visitor-desk-turn`. Open one and you find a single child span, `answer-visitor`, of type `llm`, with model `gpt-4o-mini`, the full message array that was sent, and token usage. The **Estimated cost** column is filled in: in the reference run each turn cost between about $0.000095 and $0.00011, which is why the whole demo costs a fraction of a cent.
- **Prompt growth**: every turn re-sends the history, so the prompt gets longer as the chat goes on. In the reference run the family conversation went 430, 502, 561 prompt tokens and the wheelchair one 423, 493, 564. The demo prints these numbers, and they match the span usage in Opik.
- **Feedback column**: the last trace of `wheelchair-visit` (the answer about changing a ticket) carries `visitor-satisfaction = 1`, with a reason. Sort or filter the Traces table on that column to find liked (or, with a `0`, disliked) answers.

## Run it yourself

1. `cd openai-ts-museum-visitor-desk && npm install`
2. Provide `OPENAI_API_KEY`: copy `.env.example` to `.env` and fill it in, or keep it in a repo-root `.env`, which the demo also reads.
3. Point the SDK at your Opik: `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default` (for Opik Cloud, set `OPIK_API_KEY` and `OPIK_WORKSPACE` instead).
4. `npm run demo`
5. `npm run verify` prints the traces, threads, llm spans with cost, and the feedback score from Opik.
6. Offline tests, no key and no server needed: `OPIK_TRACK_DISABLE=true npm test`. (`vitest.config.ts` sets that flag too; it makes the Opik SDK a no-op.)

## Poke around

- Add a third conversation to `src/conversations.ts` and watch a third thread appear.
- Ask something the fact sheet does not cover ("is there a cafe?") and read the trace: does the desk admit it, or invent a cafe?
- Change `toThumbs(true)` in `src/demo.ts` to `toThumbs(false)`, re-run, and sort the Traces table by `visitor-satisfaction`.
- Swap `MODEL` in `src/bot.ts` for `gpt-4.1-mini` and compare the Estimated cost column. Note the model name must be one Opik has pricing for.

## Gotchas we hit

**Symptom: the traces and spans are there, but the cost column is empty.** Cause: `opik-openai@2.2.100` (`trackOpenAI`) records each completion as a span of type `general`, and Opik only prices `llm` spans. Fix: log the span yourself with the right type, model, provider and usage keys:

```ts
const span = trace.span({ name: "answer-visitor", type: "llm", model: "gpt-4o-mini", provider: "openai", input: { messages } });
// ...call OpenAI, then:
span.update({ output, usage: { prompt_tokens, completion_tokens, total_tokens } });
span.end();
```

**Symptom: `npm install opik-openai opik` fails with `ERESOLVE`, "peer opik@^1.8.61".** Cause: `opik-openai` declares a stale peer range on the `opik` package. We no longer depend on `opik-openai`, but if you add it back, put `"overrides": { "opik-openai": { "opik": "$opik" } }` in `package.json`. It also needs `openai@^6`.

**Symptom: `trace.id` is undefined.** Cause: the TypeScript `Trace` object keeps its id under `.data`. Fix: use `trace.data.id` (the demo does, to score the right trace).

**Symptom: the last trace or the feedback score never shows up.** Cause: the SDK sends data in background batches, and `logTracesFeedbackScores` returns `void`, so there is nothing to await. Fix: `await opik.flush()` before scoring (so the trace exists) and again before the process exits; `src/feedback.ts` does both.

## How it's put together

- `src/museum.ts`: loads `data/museum.json` and builds the system prompt.
- `src/bot.ts`: `VisitorDesk`, with history, the trace per turn, the `llm` span and token usage.
- `src/tracing.ts`: the Opik client, pinned to the project name.
- `src/feedback.ts`: builds and logs `visitor-satisfaction` scores, flushing around the call.
- `src/summary.ts`: per-conversation token totals, showing the prompt growth.
- `src/conversations.ts`: the two scripted conversations.
- `src/demo.ts`: runs both conversations, scores one trace, flushes.
- `src/verify.ts`: reads the project back from Opik.
- `data/museum.json`: the fictional fact sheet.
- `tests/desk.test.ts`: offline tests with a stubbed OpenAI client, run with tracking disabled.
- `vitest.config.ts`: disables Opik tracking for tests.

---

*built with Opik · inspired by Opik's examples and documentation*
