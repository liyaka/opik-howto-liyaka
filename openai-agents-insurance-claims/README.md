# openai-agents-insurance-claims

*A claims intake desk where a triage agent hands off to specialists, and Opik shows every handoff and tool call.*

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![openai-agents 0.23](https://img.shields.io/badge/openai--agents-0.23-412991?style=flat)
![Opik 2.2.100](https://img.shields.io/badge/Opik-2.2.100-2f54eb?style=flat)

When a claim goes sideways, the final message tells you nothing: was the loss routed to the wrong
desk, did the specialist skip the coverage check, or did a tool return something the model glossed
over? This example is a small intake desk for a fictional insurer. A customer describes a loss, a
triage agent hands the conversation to an auto, home or travel-medical specialist, and the specialist
looks up the policy, checks coverage and opens a claim. Opik's official Agents SDK integration turns
each turn into a trace tree, and the SDK's `group_id` turns each conversation into an Opik thread.

## What you'll build

- Four agents on `gpt-4o-mini`: a **Triage Agent** that only routes, and **Auto**, **Home** and **Travel Medical** claims agents.
- Three tools shared by the specialists: `lookup_policy`, `check_coverage` (applies deductible and limit) and `open_claim`. They read `data/policies.json`, four invented policies, no external API.
- A demo of three two-turn conversations: the customer reports a loss and gets a coverage estimate, then asks to file.
- Tracing in two lines: `set_trace_processors([OpikTracingProcessor()])`, and `trace(..., group_id=...)` around each turn.

## See it in Opik

Open the `openai-agents-insurance-claims` project. After one clean run it holds **6 traces** (named
`Claims intake`) in **3 threads**: `auto-fender-bender-*`, `home-burst-pipe-*` and `travel-er-visit-*`.

- **First turn of a conversation** (14 spans): a `Task` root, then `Triage Agent` with one `llm` span, a
  `Handoff` span, then the specialist (for example `Auto Claims Agent`) with its turns in order:
  `llm`, `lookup_policy` (`tool`), `llm`, `check_coverage` (`tool`), `llm`. Click a tool span to see the
  arguments the model chose and the JSON the tool returned, e.g. an estimated payout of 1800 for a 2300 collision loss after a 500 deductible.
- **Second turn** (7 spans): no triage and no handoff. It starts at the specialist, calls `open_claim`
  (`tool`) and writes the confirmation with the claim id.
- **Threads tab**: three rows, each with two turns. Open one to read the whole conversation in order.
- **Cost**: every `llm` span has token usage and a non-null `total_estimated_cost` (about 0.00004 to 0.00012 USD each, about 0.002 USD for the whole run).

## Run it yourself

1. Start Opik locally (or point `~/.opik.config` at Comet cloud) and have an OpenAI key.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` one level up also works).
3. `uv sync`
4. `uv run main.py` (about 30 seconds)
5. Open the project in Opik as described above.
6. Tests, offline: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change the first message of a conversation to something ambiguous ("my car was in the garage when the pipe burst") and watch which way the handoff span goes.
- Ask for an uncovered loss (`flood` on `AUT-20417`) or use `AUT-31188`, an inactive policy, and compare the `check_coverage` tool span with what the specialist tells the customer.
- Add a fourth specialist (pet insurance) in `desk.py` and confirm its handoff appears with no tracing change.
- Remove `group_id` from `trace(...)` in `main.py`: the Threads tab loses the conversations and each turn becomes a lone trace.

## Gotchas we hit

**Follow-up turns show no handoff and no tool spans, and the agent forgets what it was doing.**
Symptom: the second trace of a thread contains only `Triage Agent` and one `llm` span, and the reply
is generic ("your claim has been filed") or claims a claim id that no `open_claim` span created.
Cause: `Runner.run_sync(triage_agent, history)` always starts at the agent you pass, so each turn
restarts at triage. Fix: resume with the agent that finished the last turn.

```python
result = Runner.run_sync(agent, history + [{"role": "user", "content": message}])
agent = result.last_agent
```

**The specialist opens the claim before the customer asks.** Symptom: the first trace of a thread already
contains an `open_claim` tool span. Cause: with "open a claim when asked" in a prompt, `gpt-4o-mini` reads a
loss report as the request. Fix: tell the agent to report coverage first and call `open_claim` only after an explicit request in a later turn (see `desk.py`).

## How it's put together

- `main.py` — scripted conversations, Opik processor setup, one `trace(group_id=...)` per turn, flush at exit.
- `desk.py` — the triage agent, three specialists and the function-tool wrappers.
- `tools.py` — plain policy lookup, coverage and claim logic, no model calls.
- `data/policies.json` — the fictional policy book.
- `tests/test_tools.py` — coverage maths, refusals and claim opening.
- `tests/test_desk.py` — handoff wiring, and a tool invoked through the SDK wrapper with tracking disabled.
- `.env.example` — keys and Opik settings with where to get them.

---

*built with Opik · inspired by Opik's examples and documentation*
