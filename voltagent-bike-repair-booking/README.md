# voltagent-bike-repair-booking

*A bike-shop booking assistant on VoltAgent, where the interesting part is the 40 lines that make Opik show what each LLM call cost.*

![Node](https://img.shields.io/badge/node-20.16%2B-339933?style=flat&logo=node.js&logoColor=white)
![VoltAgent](https://img.shields.io/badge/%40voltagent%2Fcore-2.11-1b1f23?style=flat)
![Tests](https://img.shields.io/badge/tests-vitest-6E9F18?style=flat)

## The problem

VoltAgent already emits OpenTelemetry spans, and Opik already accepts OTLP. Point one at the other and traces do show up, which is what makes the next part easy to miss: every span arrives as `general`, with no model, no token counts and no dollar figure, and the trace's input column is a dump of internal attributes. The two sides use different attribute names (`llm.usage.prompt_tokens` on one, `gen_ai.usage.prompt_tokens` on the other), and Opik will not price a call unless it also knows the provider. This example shows the mapping that closes that gap, and a script that proves it did.

## What you'll build

A booking assistant for a fictional neighbourhood shop, Spokewise Cycle Works, running on `gpt-4o-mini`. It has four tools over a small JSON dataset in `data/shop.json`: `check_service_menu`, `find_open_slot`, `book_repair` and `get_booking_status`. Nothing but the model call leaves your machine.

The Opik part lives in `src/telemetry/`. An exporter wrapper rewrites every VoltAgent span just before it goes out over OTLP: llm spans get `gen_ai.request.model`, `gen_ai.provider.name = openai` and `gen_ai.usage.*`; tool spans get `gen_ai.tool.call.arguments` and `.result`; the agent span keeps just `input` and `output`. `npm run check` then reads the project back through Opik's REST API and fails if any llm span lacks provider, usage or a non-null cost.

## See it in Opik

Run the demo, then open the `voltagent-bike-repair-booking` project (workspace `default` on a local install). It holds three traces, one per customer message, 11 spans in all.

- **Traces tab.** Each row is named `spokewise-booking-assistant`; the input column reads like the customer's sentence (for example "I'd like the basic tune-up for my green hybrid...") and the output column holds the assistant's reply. The cost column is filled: roughly $0.00012 to $0.00014 per trace, about $0.0004 for the three.
- **The booking trace.** Open the tune-up request. The tree has one `llm:generateText` span of type llm (provider `openai`, model `gpt-4o-mini`, 704 prompt tokens, about $0.00014) and three tool spans: `check_service_menu`, `find_open_slot` and `book_repair`. The `book_repair` span shows `slot_id: SLOT-3` going in and booking `BK-2203` coming out, so a wrong booking can be traced to the exact arguments the model chose.
- **The llm span's output is empty.** VoltAgent does not record the completion on its llm span, so the reply shows only at trace level. Usage, model, provider and cost are all there.

To see the difference the mapping makes, run the demo with `OTEL_GENAI_MAPPING=off`: the same three traces arrive, but all 11 spans are `general`, none has a model, usage or cost, and the trace input column is a wall of `operation.id`, `entity.type` and friends.

## Run it yourself

1. `cp .env.example .env`, add `OPENAI_API_KEY`, and set `OPIK_URL_OVERRIDE=http://localhost:5173/api` for a local Opik (leave it unset for Opik Cloud and fill in `OPIK_API_KEY` and `OPIK_WORKSPACE`). Or reuse a repo-level `.env`, which is read as a fallback.
2. `npm install`
3. `npm run demo`: three scripted customer messages, about 15 seconds, well under a cent.
4. `npm run check`: queries Opik and prints one line per llm and tool span, ending in `OK: usage and cost present on every llm span` or a list of what is missing.
5. `npm test`: offline tests. They need no keys and send nothing to Opik; set `OPIK_TRACK_DISABLE=true` to make `createObservability()` install no exporter at all. `npm run typecheck` runs `tsc`.

## Poke around

- Run `OTEL_GENAI_MAPPING=off npm run demo`, then `npm run check`. It fails with "no llm spans", which is the whole lesson in one command.
- In `src/telemetry/setup.ts`, change the provider from `"openai"` to `"openai.responses"`, rerun and check: usage still lands but every cost is null.
- Ask for something the shop cannot do, such as an evening slot. Open the `find_open_slot` span and see how the model copes with an empty result.
- Add a fifth tool in `src/tools.ts` and add its name to the demo prompt. It appears as a tool span with no tracing code of its own.

## Gotchas we hit

**Spans arrive but every one is `general`, with no usage or cost.** VoltAgent names its attributes `llm.model` and `llm.usage.*`; Opik only reads `gen_ai.*`. Wrap the OTLP exporter and rewrite attributes before export (`src/telemetry/mapping.ts`), e.g. `attrs["gen_ai.usage.prompt_tokens"] = attrs["llm.usage.prompt_tokens"]`. The wrapper needs OpenTelemetry 2.x (`@opentelemetry/sdk-trace-base ^2`), the version VoltAgent builds on.

**Usage is there but `total_estimated_cost` is null.** Opik prices a span only when the provider is one it knows. VoltAgent's llm spans carry none, and a provider such as `openai.responses` (what some other frameworks send) is not priced either. Set `gen_ai.provider.name` to `openai` next to a model name Opik has prices for, here `gpt-4o-mini`.

**The trace input column is a pile of `operation.id`, `entity.type`, `agent.instructions`...** Any attribute Opik has no rule for is stored in the span input. Do not just add attributes: reduce each span type to what should show, as `mapVoltAgentAttributes` does, and move extras to `opik.metadata.*`.

**Last spans missing from Opik.** `BatchSpanProcessor` exports in the background, so a script that exits right after the last call loses its tail. Call `await observability.shutdown()` before exiting, as `src/demo.ts` does.

## How it's put together

- `data/shop.json`: the fictional shop's services, slots and two existing bookings.
- `src/shop/store.ts`: pure shop logic (menu search, slot lookup, booking, status), no framework.
- `src/tools.ts`: the four VoltAgent tools, thin wrappers over the shop.
- `src/agent.ts`: the agent definition, model and instructions; knows nothing about tracing.
- `src/telemetry/mapping.ts`: the pure VoltAgent-to-`gen_ai.*` attribute translation.
- `src/telemetry/exporter.ts`: the exporter wrapper that applies it just before OTLP export.
- `src/telemetry/setup.ts`: OTLP endpoint, workspace and project headers, the `OTEL_GENAI_MAPPING` and `OPIK_TRACK_DISABLE` switches.
- `src/demo.ts`: the scripted demo runner; it flushes the exporter on exit.
- `src/check.ts`: reads the project back from Opik and asserts usage, provider and cost.
- `tests/store.test.ts`, `tests/mapping.test.ts`: shop logic, the attribute mapping, the exporter wrapper with a stub, and a tool run with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
