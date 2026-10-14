# n8n-food-bank-volunteers

**A volunteer-screening workflow built on the n8n canvas, traced into Opik without a single line of instrumentation.**

[![n8n](https://img.shields.io/badge/n8n-2.41.7-ea4b71?style=flat)](https://n8n.io)
[![n8n-observability](https://img.shields.io/badge/n8n--observability-1.0.3-6b46c1?style=flat)](https://www.npmjs.com/package/n8n-observability)
[![model](https://img.shields.io/badge/model-gpt--4o--mini-10a37f?style=flat)](https://platform.openai.com/docs/models/gpt-4o-mini)
[![runs in](https://img.shields.io/badge/runs_in-Docker-2496ed?style=flat)](https://docs.docker.com/compose/)

Riverbend Community Food Bank (fictional) gets volunteer sign-ups from a web form. A coordinator used to read each one and decide where the person fits; now an n8n workflow does a first pass with gpt-4o-mini and hands back a short card: approve, follow up, or not a fit, plus a suggested shift and the question to ask next.

Workflows like this are built by whoever runs operations, not by engineers, and they fail quietly. When a volunteer gets turned away, nobody can say whether the form sent bad data, an expression on the canvas broke, or the model simply reasoned badly. This example makes every execution show up in Opik as a trace with one span per node, so that question has an answer.

## What you'll build

A self-hosted n8n with four nodes: **Sign-up webhook → Screen volunteer (gpt-4o-mini) → Build coordinator card → Reply to form**. The screening prompt encodes Riverbend's shift rules (warehouse and pantry 16+, front desk 18+, delivery driver 21+ with a licence, under-16s only on family-packing day with a guardian).

Opik comes in through the Docker image, not the workflow. `Dockerfile` installs the `n8n-observability` package and points n8n's `EXTERNAL_HOOK_FILES` at its hooks; `docker-compose.yml` tells the hooks where Opik's OTLP endpoint is and which project to write to. The canvas has no tracing nodes and no code.

## See it in Opik

Open the **n8n-food-bank-volunteers** project. After `./demo.sh` there are **4 traces**, all named `Volunteer screening`, one per sign-up. Each has **5 spans**: the workflow span at the root and one span per node.

Click the `Screen volunteer (gpt-4o-mini)` span and read its **Input** panel. Two attributes do the work:

- `n8n.node.input` is the item the node received, including the webhook `body` exactly as the form posted it.
- `n8n.node.output` is what the model returned: `decision`, `suggested_shift`, `reason`, `follow_up_question`.

Now find Priya Raman's trace. She is a retired school-bus driver who asked to drive the delivery van. The card she got back says `not_a_fit`, with the reason *"The volunteer is not eligible for the delivery driver shift as they must be at least 21 years old."* The span shows `'age': '67'` arriving in `n8n.node.input`, so the form and the expressions are fine: the model misapplied a minimum-age rule to someone well above it. Without the trace you would have one wrong card and three plausible guesses about where it went wrong; with it, the fault is pinned to the prompt and the model in one click.

The other three behave as intended in our run: Owen (15) gets `follow_up` about the guardian-only family day, Marisol's vague sign-up gets `follow_up` asking her age, and Grant, who is selling inventory software, gets `not_a_fit`.

## Run it yourself

1. Put `OPENAI_API_KEY` in the repo-root `.env` (or export it). For a local Opik nothing else is needed; for Opik Cloud also set `OPIK_OTLP_ENDPOINT`, `OPIK_WORKSPACE` and `OPIK_API_KEY` (see `.env.example`).
2. Make sure Opik is reachable. The default endpoint, `http://host.docker.internal:5173/api/v1/private/otel`, is a self-hosted Opik running on the same machine.
3. `./setup.sh` builds the image, starts n8n on `localhost:5678`, creates the owner account and the OpenAI credential, then imports and activates the workflow.
4. `./demo.sh` posts four sample sign-ups and prints each coordinator card.
5. Open the `n8n-food-bank-volunteers` project in Opik.

`docker compose down -v` stops n8n and deletes its data volume.

## Poke around

- **Fix Priya.** Log in at `localhost:5678` (`coordinator@example.org` / `Riverbend-demo-1`), change the driver rule in the system message to "age 21 or older", run `./demo.sh` again and compare her two `Screen volunteer` spans side by side.
- **Break an expression instead.** Rename `notes` to `about` in one `demo.sh` payload. The trace shows the empty field arriving at the model, which is a different failure from Priya's and is told apart the same way.
- **Raise the temperature** in the OpenAI node options and send the same sign-up several times; the per-execution outputs in Opik show how stable the verdict is.
- **Read the non-LLM spans.** `Build coordinator card` shows the expressions' results, which is where you debug a mapping mistake without re-running the workflow.

## Gotchas

**The spans have no model, token usage or cost.** With n8n 2.41.7 and n8n-observability 1.0.3, every span arrives as type `general` and no `gen_ai.*` attributes reach Opik, so the Usage and Cost columns stay empty. Prompts and outputs are captured (as the `n8n.node.*` attributes above); spend is not. If cost matters, take it from the OpenAI usage dashboard for now.

**Input and Output show as attribute dumps, not clean text.** The hooks export node data as span attributes, so Opik files them under Input (`n8n.node.input`, `n8n.node.output`, `n8n.node.parameters.*`) and the Output column stays empty. Expand the span's Input to read them.

## How it's put together

- `Dockerfile`: the `n8nio/n8n` image plus `n8n-observability`, with `EXTERNAL_HOOK_FILES` pointing at its hooks.
- `docker-compose.yml`: runs n8n and sets the OTLP endpoint and headers (`Comet-Workspace`, `projectName`) for the hooks.
- `workflow/volunteer-screening.json`: the four-node workflow; the credential id is a placeholder filled in at import time.
- `setup.sh`: headless setup through n8n's REST and public API (owner account, API key, OpenAI credential, import, activate).
- `demo.sh`: posts four fictional sign-ups to the webhook.
- `.env.example`: the variables `setup.sh` and the compose file read.

---

*Built with [Opik](https://github.com/comet-ml/opik) · inspired by Opik's examples and [documentation](https://www.comet.com/docs/opik/)*
