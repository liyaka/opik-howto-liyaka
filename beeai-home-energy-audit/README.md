# beeai-home-energy-audit

*A BeeAI ReAct agent that triages "why is my bill so high?" complaints, with the think, tool, observe loop readable in Opik.*

![Node](https://img.shields.io/badge/node-18%2B-339933?style=flat&logo=node.js&logoColor=white)
![BeeAI](https://img.shields.io/badge/beeai--framework-0.1.13-f5c518?style=flat)
![Tests](https://img.shields.io/badge/tests-vitest-6e9f18?style=flat)

A utility customer says "our bill doubled" or "the heat pump keeps short-cycling". A good auditor does not guess: they pull the meter history, look at what is plugged in, check the tariff, and only then rank fixes by payback. A ReAct agent does the same thing, but `agent.run()` hands you back one string and hides the loop, so when the advice is wrong you cannot tell whether it read the wrong data, ignored the data, or priced something irrelevant. This example wires BeeAI's OpenInference instrumentation to Opik over plain OTLP so each iteration, model call and tool call is a span you can open.

## What you'll build

A TypeScript agent on `gpt-4o-mini` with four tools over a small fictional dataset in `data/households.json` (three households, two tariffs, seven candidate fixes):

- `get_meter_readings` - six months of kWh and the month-over-month change
- `get_appliance_inventory` - wattage, run hours, estimated kWh per month, notes, and the fix ids that apply
- `lookup_tariff` - peak and off-peak price, peak window, fixed fee
- `estimate_savings` - monthly saving, upfront cost and payback for one fix

`npm run demo` runs three complaints and prints a prioritized fix list for each:

| Household | Complaint | What the data says |
| --- | --- | --- |
| HH-101 | bill doubled in January | EV charger added on 2025-12-28 on an evening-peak tariff |
| HH-102 | heat pump short-cycles | oversized 5-ton unit, 14-month-old filter, clogged coil |
| HH-103 | high bill in a quiet winter | pool pump running 24 hours a day under a cover |

## See it in Opik

Open the **beeai-home-energy-audit** project (workspace `default`) and look at the Traces tab. After one demo run there are three traces, each named `beeai-framework-main`. The Input column is the full audit prompt (household and complaint) and the Output column is the agent's final answer, for example the HH-101 trace ends with "Schedule EV charging to start after 21:00 - saves $189/month, costs $0".

Open the HH-101 trace. It has 74 spans: 10 of type `llm`, the rest `general`. The tree has five `iteration-N` spans directly under the root, one per ReAct turn. Sorted by start time, each of iterations 1 to 4 is followed by a model call (`backend.openai.chat.start` / `success`, type `llm`, model `gpt-4o-mini`) and a `tool.dynamic.<name>.start` / `success` pair (these hang off BeeAI's `agent.react.*` event spans rather than directly under the iteration), in order: `getMeterReadings`, `getApplianceInventory`, `lookupTariff`, `estimateSavings`. The tool span's input shows the arguments the model chose (`{"household_id": "HH-101"}`), and the `success` span's output holds what the tool returned, such as the EV charger row and the list `candidate_fixes: ["ev-offpeak-schedule"]`. Iteration 5 is the model writing the final list. The HH-102 and HH-103 traces run 7 iterations and 106 spans because the agent prices three fixes instead of one.

BeeAI emits many small event spans (`agent.react.update-N`, `partialUpdate-N`, `*.finish-N`); collapse them and follow the `iteration-N` rows. Tool spans are type `general`, not `tool`, because the instrumentation does not set a tool-typed attribute that Opik maps.

Token usage and cost: one `llm` span per trace carries usage and a cost (about 2,100 prompt and 140 completion tokens, roughly $0.0004 for the HH-101 run's last call). BeeAI's instrumentation reports usage once, for the last model call, so trace totals understate the whole loop; the dollar figure is Opik's estimate from `gpt-4o-mini` pricing.

## Run it yourself

1. Start Opik locally (or point at your own OTLP endpoint, see `.env.example`).
2. `cp .env.example .env` and set `OPENAI_API_KEY`.
3. `npm install`
4. `npm run demo` - about 30 seconds and well under a cent.
5. Open the `beeai-home-energy-audit` project in Opik and click a trace.

Tests need no keys and no Opik: `npm test` (14 vitest tests in a couple of seconds).

## Poke around

- Change HH-102's complaint to "the condo is cold in the morning" and compare the `iteration-N` count with the original trace.
- In `data/households.json`, delete the EV charger from HH-101 and rerun: the `getApplianceInventory` output changes and so does the diagnosis, so you can see which tool result drove the answer.
- Set `maxIterations` to 3 in `src/agent.ts`: the loop is cut off before the pricing tools can run, which is what an under-budgeted agent looks like in the trace.
- Remove `providerTagger` from `src/tracing.ts` and rerun: usage still lands, `total_estimated_cost` goes back to null.

## Gotchas we hit

- **`ERR_MODULE_NOT_FOUND: Cannot find package '@ai-sdk/openai'`** on the first run. `beeai-framework` loads its OpenAI adapter through this package but does not install it. Fix: `npm install @ai-sdk/openai@^1.3.13` (it is in `package.json` here).
- **The final answer is `Function Name: get_appliance_inventory Function Input: {...}`** and the run ends after one tool call. `gpt-4o-mini` sometimes starts a step with the function call instead of a `Thought:` line, and BeeAI's ReAct parser then treats the text as the answer. Fix: tell the model in the prompt that every step starts with a `Thought:` line (see `buildPrompt` in `src/agent.ts`).
- **Usage is there but `total_estimated_cost` is null.** The OpenInference spans carry the provider and token counts under keys Opik's price table does not read, and the model name is missing from the span that holds usage. Fix: a span processor in `src/tracing.ts` sets `gen_ai.system=openai` and `gen_ai.request.model` on the model-call spans, and renames `llm.token_count.*` to `gen_ai.usage.input_tokens` / `output_tokens` / `total_tokens`.
- **The agent keeps pricing fixes that make no sense for the house** (a pool pump timer for a townhouse with no pool) until it hits `maxIterations`. When every fix id was advertised as valid, the model tried them all. Fix: `get_appliance_inventory` returns `candidate_fixes` for that household and `estimate_savings` answers an inapplicable fix with an error listing the applicable ones.

## How it's put together

- `src/tracing.ts` - OTel `NodeSDK`, BeeAI's OpenInference instrumentation, the OTLP exporter aimed at Opik (project and workspace as headers), and the span processor that makes cost land.
- `src/agent.ts` - the audit prompt and the `ReActAgent` on `gpt-4o-mini`.
- `src/tools.ts` - the four BeeAI tools.
- `src/household.ts` - loads the dataset and holds the pure logic: readings, appliance kWh, savings maths.
- `src/config.ts` - the model name shared by the agent and the tracing setup.
- `src/demo.ts` - loads `.env`, starts tracing, runs the three complaints, flushes.
- `data/households.json` - fictional households, tariffs and fixes.
- `tests/household.test.ts`, `tests/tools.test.ts` - data logic, tools and prompt; `tests/tracing-disabled.test.ts` - tools still run with `OTEL_SDK_DISABLED=true` (the OTel switch that stops all span export) and the cost-mapping processor.
- `.env.example` - the variables the example reads.

---

*built with Opik · inspired by Opik's examples and documentation*
