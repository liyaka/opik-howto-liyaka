<div align="center">

# Larkspur Bank Assistant, Step by Step

**`mastra-banking-agent`**

*A Mastra retail-banking assistant whose every tool call, argument and result shows up as its own span in Opik.*

![Node](https://img.shields.io/badge/node-20.16%2B-339933?style=flat&logo=node.js&logoColor=white)
![Mastra](https://img.shields.io/badge/%40mastra%2Fcore-1.74-0b0b0b?style=flat)
[![Opik](https://img.shields.io/badge/Opik-OTel%20ingestion-2f54eb?style=flat)](https://github.com/comet-ml/opik)

</div>

---

A banking assistant that can freeze a card is an agent you want to be able to audit. When a customer says "my wallet was stolen, freeze my debit card", the transcript only tells you what the bot said it did. The trace should tell you what it actually did: which tool it called, with which card id, and what the bank system answered. This example is a small assistant for Larkspur Credit Union, a fictional bank, built with [Mastra](https://mastra.ai/) and exported to Opik over OpenTelemetry. The agent code and the tools never mention tracing; one exporter in `src/mastra.ts` does all of it.

## What you'll build

One Mastra `Agent` on `gpt-4o-mini` with three tools over fictional accounts in `data/`:

- `get_balance` returns an account's balance plus its cards and their status.
- `list_transactions` returns the newest transactions on an account.
- `freeze_card` blocks a card (state is held in memory for the run).

`npm run demo` plays three customer requests: a balance check, a transaction review, and a stolen-wallet card freeze for a customer who holds both a debit and a credit card.

## See it in Opik

Open the **`mastra-banking-agent`** project and the **Traces** tab. After one run there are 3 traces, all named `invoke_agent larkspur-banking-agent`, and 49 spans in total (14, 14 and 21 in my run; the model decides how many steps it takes, so your counts may differ by a few).

Open the stolen-wallet trace and expand it. The tree is `invoke_agent` > `model_generation` > one `agent_step` per loop iteration. Each step holds a `chat gpt-4o-mini` span (type `llm`) and, when the model asked for a tool, an `execute_tool` span (type `tool`):

```
invoke_agent larkspur-banking-agent
  model_generation gpt-4o-mini
    agent_step   -> chat gpt-4o-mini, execute_tool get_balance
    agent_step   -> chat gpt-4o-mini, execute_tool freeze_card
    agent_step   -> chat gpt-4o-mini            (the final reply)
```

Click `execute_tool freeze_card`: the input shows `gen_ai.tool.call.arguments` with the real `card_id` (`CRD-9021`) and the reason the model wrote, and the output shows `gen_ai.tool.call.result` with `"status": "frozen"` and the replacement-card message. Click `execute_tool get_balance` in the same trace to see where that card id came from. The model never saw it in the customer's message, it read it from the tool result. Each `llm` span carries prompt and completion tokens (for example 401 prompt and 19 completion on the first step of that trace), and the trace row sums them.

In the same stolen-wallet scenario the model sometimes freezes both of Desmond's cards even though he only asked about the debit card. When that happens the trace shows two `execute_tool freeze_card` spans, `CRD-9021` and `CRD-9022`, which is the evidence you need to tell an over-eager model from a bad tool.

## Run it yourself

1. `npm install`
2. `cp .env.example .env` and set `OPENAI_API_KEY`. For Opik Cloud also set `OPIK_API_KEY` and `OPIK_WORKSPACE_NAME`. For a local Opik set `OPIK_URL_OVERRIDE=http://localhost:5173/api` and `OPIK_WORKSPACE_NAME=default`, and leave the key empty.
3. `npm run demo` (about 15 seconds and well under one cent of gpt-4o-mini).
4. Open the `mastra-banking-agent` project in Opik and click the newest trace.
5. `npm test` runs the offline tests (no keys needed). Set `OPIK_TRACK_DISABLE=true` to turn the exporter off entirely.

## Poke around

- Change the third request in `src/demo.ts` to ask for the credit card only and compare the `freeze_card` arguments.
- Ask about `ACC-9999` and read the `get_balance` result span: the error object is what the model paraphrases.
- Add a fourth tool in `src/tools.ts` and register it in `src/agent.ts` under a snake_case key. It appears as `execute_tool <key>` with no tracing code at all.
- Set `maxSteps: 1` in `src/demo.ts` and watch the tree collapse to a single `chat` span that never reaches a tool.

## Gotchas we hit

**The span is called `execute_tool getBalanceTool`, not `get_balance`.** Mastra names the span after the key in the agent's `tools` map, not after the tool's `id`. Register tools as `tools: { get_balance: getBalanceTool, ... }` so the name in Opik matches the tool name the model sees.

**The trace-level Output column is empty.** Mastra's OTel mapping puts the request in the root span's input attributes and never sets an output on the trace, so the trace row shows `output: None`. The final answer is not lost, but it is only in the console and in the last `chat` span, not in the trace row. Nothing in this example maps it; if you need it there, add a span processor or log the answer on the root span yourself.

**Cost is empty even though token usage is there.** The `chat` spans arrive with usage and the model name, but their provider attribute is `openai.responses`, which Opik does not recognise, so `total_estimated_cost` stays null. Usage is real, the dollar figure is something you derive from it (or fix by mapping the provider attribute to `openai` in a span processor).

## How it's put together

- `data/accounts.json`, `data/transactions.json` - the fictional customers, cards and transactions.
- `src/bank.ts` - plain lookup, listing and card-freeze logic over that data.
- `src/tools.ts` - the three Mastra tools wrapping `bank.ts`.
- `src/agent.ts` - the Larkspur agent: instructions, model, tools.
- `src/mastra.ts` - the Mastra instance and the Opik `OtelExporter` (the only file that knows about tracing).
- `src/demo.ts` - loads env vars, runs the three requests, flushes the exporter.
- `tests/bank.test.ts`, `tests/tools.test.ts` - offline vitest tests for the bank logic, a tool called with tracking disabled, and the tracing switch.

---

*built with Opik · inspired by Opik's examples and documentation*
