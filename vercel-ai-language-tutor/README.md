# vercel-ai-language-tutor

*A streaming Spanish tutor on the Vercel AI SDK, where every reply is traced into Opik and graded by a judge that runs on the server, not in your code.*

![TypeScript](https://img.shields.io/badge/typescript-5.6%2B-3178C6?style=flat&logo=typescript&logoColor=white)
![Next.js](https://img.shields.io/badge/next.js-16-000000?style=flat&logo=nextdotjs&logoColor=white)
![AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat)
![opik-vercel](https://img.shields.io/badge/opik--vercel-2.2.100-2f54eb?style=flat)

A chat tutor is easy to demo and hard to supervise. Replies stream out token by token, a "session" is really a string of separate HTTP requests, and whether the tutor actually fixed the learner's mistake is a judgement call nobody reads one by one. This example wires up all three problems at once: streaming spans, one Opik thread per learner session, and an online-evaluation rule (LLM-as-judge) that scores every trace after it lands.

## What you'll build

"Profe Marisol" is a Spanish tutor for an English speaker, driven by small fictional lesson plans in `data/lessons.json` (a cafe in Valparaiso, weekend plans). The learner can write Spanish and get corrected, ask for a phrase translation, or ask for a three-question quiz. The pieces are deliberately separate: the persona and lesson data are plain modules, the route handler only parses the request and calls `streamText`, and the Opik wiring lives in one telemetry module plus one rule module. A scripted client plays two multi-turn sessions so you never have to type.

```
demo script -> find-or-create judge rule -> next dev -> POST /api/chat x6 (2 sessions)
                                                          |-> streamText(gpt-4o-mini) streams back
                                                          '-> OTel spans -> OpikExporter -> Opik
Opik server: new trace -> tutor_reply_quality judge -> feedback score on the trace
```

## See it in Opik

Open the `vercel-ai-language-tutor` project. In a clean run the Traces tab holds 6 traces named `tutor-turn`. Each has a `llm` span (`chat gpt-4o-mini`, resolved to `gpt-4o-mini-2024-07-18`) inside a `general` step span. The llm span has token usage (270 to 436 total tokens per turn) and a real estimated cost of roughly $0.00006 to $0.00009, so cost is not null. The input shows the system prompt (persona plus lesson) and the whole history, which is why later turns cost slightly more.

The Threads tab shows 2 threads of 3 turns each, one per scripted learner session. The thread id is the chat id the client sends; the route passes it as `runtimeContext.threadId` and the telemetry module copies it into the span attributes Opik reads.

The `tutor_reply_quality` column is filled by the rule, not by the app: Rules in the project settings lists one enabled LLM-as-judge rule with sampling rate 1. In the verified run all six replies were scored (five 10s and one 9). The judge was lenient: it passed the mistake correction, the translation and both quizzes. The same project also shows traces named `online_evaluation`: those are the judge's own runs, one per scored trace.

## Run it yourself

1. A local Opik is running (workspace `default`) and your OpenAI key is registered under Opik's LLM provider settings, because the judge runs inside Opik.
2. `cp .env.example .env`, add `OPENAI_API_KEY` (or rely on a repo-root `.env`), `npm install`.
3. `npm run demo`: creates the rule if missing, starts the dev server on port 3181, plays both sessions, shuts it down (about 25 seconds).
4. `npm run verify`: polls until every tutor trace has a `tutor_reply_quality` score, then prints traces, threads, llm-span cost and scores.
5. Optional: `npm run dev` and chat at http://localhost:3181 (a new page load is a new thread).

## Poke around

- Edit the judge text in `lib/rule.ts`, make it harsher (for example require an English explanation under 20 words) and run `npm run rule` then `npm run demo` again to see the score distribution move.
- Add a third session to `scripts/sessions.ts` where the learner asks something off-topic and see how the judge grades the tutor's refusal.
- Switch the model in `app/api/chat/route.ts` to `gpt-4.1-mini` and compare the cost column.
- Run `npm run rule` twice and open the Rules tab: still one rule.

## Gotchas we hit

- **`ERESOLVE ... peer opik@"^1.8.75" from opik-vercel@2.2.100` on `npm install`.** `opik-vercel` still declares a stale peer dependency on the 1.x `opik` package, so `opik` 2.2.100 conflicts with it. Keep `"opik": "2.2.100"` and add an npm override so `opik-vercel` uses it: `"overrides": { "opik-vercel": { "opik": "$opik" } }`. Tracing, threads and cost work normally with it.
- **The project stays empty although the exporter is configured (AI SDK 7).** v7 does not emit OpenTelemetry spans until a telemetry integration is registered, and thread ids need a runtime context. Call `registerTelemetry(new OpenTelemetry({ usage: true, enrichSpan }))` in `instrumentation.ts` and pass `runtimeContext` plus `includeRuntimeContext` on the call (see `lib/telemetry.ts`).
- **The rule scores nothing, or the judge traces say "API key not configured".** The judge uses the provider key stored in Opik's server-side LLM provider settings, and a rule only scores traces that arrive after it is enabled. Register the key first, create the rule before sending traffic (`ensureRule` runs at the start of `npm run demo`), and when re-running delete the old traces, not the rule.
- **Trace counts are double what you sent.** On this Opik version the judge's runs are logged into the same project as traces named `online_evaluation`. Filter them out when counting (`scripts/verify.ts` does).

## How it's put together

- `app/api/chat/route.ts`: thin route handler, `streamText` with the persona and telemetry settings.
- `app/page.tsx`, `app/layout.tsx`: minimal `useChat` page.
- `lib/persona.ts`: tutor system prompt built from a lesson.
- `lib/lessons.ts`, `data/lessons.json`: fictional lesson plans and vocab.
- `lib/telemetry.ts`: `OpikExporter`, `registerTelemetry`, span enrichment and per-call settings.
- `lib/rule.ts`, `lib/opik-api.ts`: find-or-create the online-evaluation rule over Opik's REST API.
- `instrumentation.ts`: Next.js startup hook that registers telemetry in the Node runtime.
- `scripts/demo.ts`, `scripts/sessions.ts`: scripted multi-turn client; `scripts/verify.ts`: waits for and prints the scores; `scripts/ensure-rule.ts`: rule setup on its own.
- `tests/`: offline vitest tests for lessons, persona, telemetry settings and rule find-or-create. `npm test` sets `OPIK_TRACK_DISABLE=true`, which is how the Opik TypeScript SDK turns tracking off; no keys needed.

---

*built with Opik · inspired by Opik's examples and documentation*
