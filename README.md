# opik-howto-liyaka

**Twenty-two small LLM apps, each wired into [Opik](https://github.com/comet-ml/opik) to answer one question you will eventually ask about your own app.**

[![examples](https://img.shields.io/badge/examples-22-2f54eb?style=flat)](#the-examples)
[![python](https://img.shields.io/badge/Python-12-3776ab?style=flat)](#the-examples)
[![typescript](https://img.shields.io/badge/TypeScript-8-3178c6?style=flat)](#the-examples)
[![license](https://img.shields.io/badge/license-Apache--2.0-green?style=flat)](LICENSE)

Why did the bot tell a 67-year-old she was too young to drive? Which of two models is ten times more expensive on your workload? Did the retry actually happen, and in which process? Is prompt v2 better than v1, or does it just feel better?

Each folder here is a complete, runnable app with fictional data, built around one of those questions. The README in each folder tells you which Opik project, trace and span to open, and what you should see there, using the numbers from a real run. Where a run failed or an integration fell short, the README says so.

## The examples

**Conversations and threads**

| Example | Stack | What you'll see in Opik |
|---|---|---|
| [openai-ts-museum-visitor-desk](openai-ts-museum-visitor-desk) | TypeScript · OpenAI SDK | multi-turn chats grouped into threads, cost per turn, a feedback score on a trace |
| [langchainjs-fastify-library-picks](langchainjs-fastify-library-picks) | TypeScript · LangChain.js + Fastify | threads that read as clean transcripts, catalog lookups as tool spans |
| [vercel-ai-language-tutor](vercel-ai-language-tutor) | TypeScript · Vercel AI SDK + Next.js | streaming spans, threads, and an online LLM-judge rule scoring every reply server-side |

**Agents and tool calls**

| Example | Stack | What you'll see in Opik |
|---|---|---|
| [openai-agents-insurance-claims](openai-agents-insurance-claims) | Python · OpenAI Agents SDK | triage handing off to specialist agents, tool spans, threads via `group_id` |
| [mastra-banking-agent](mastra-banking-agent) | TypeScript · Mastra | agent loops with real `execute_tool` spans and their arguments |
| [beeai-home-energy-audit](beeai-home-energy-audit) | TypeScript · BeeAI + OpenInference | a ReAct loop (think, act, observe) laid out iteration by iteration |
| [smolagents-weather-station-analyst](smolagents-weather-station-analyst) | Python · smolagents | the pandas code a CodeAgent wrote and ran, next to its execution logs |
| [langgraph-wildlife-field-report](langgraph-wildlife-field-report) | Python · LangGraph | one deep trace with a planner/researcher loop in the agent-graph view, cost per agent |
| [voltagent-bike-repair-booking](voltagent-bike-repair-booking) | TypeScript · VoltAgent | a `gen_ai.*` attribute mapping that turns raw OTel spans into priced LLM spans |

**Retrieval**

| Example | Stack | What you'll see in Opik |
|---|---|---|
| [llamaindex-syllabus-qa](llamaindex-syllabus-qa) | Python · LlamaIndex | retrieve and synthesize spans over generated PDFs, plus a test suite |
| [ollama-beekeeping-rag](ollama-beekeeping-rag) | Python · LangChain + Ollama | a fully local RAG app traced end to end with zero cloud LLM calls |
| [quarkus-langchain4j-pharmacy-faq](quarkus-langchain4j-pharmacy-faq) | Java · Quarkus LangChain4j | JVM traces over OTLP with prompt and completion text on the LLM spans |

**Evaluation, test suites and prompts**

| Example | Stack | What you'll see in Opik |
|---|---|---|
| [anthropic-ts-boardgame-rules-qa](anthropic-ts-boardgame-rules-qa) | TypeScript · Anthropic SDK | a test suite with plain-English citation assertions, pass/fail per item |
| [pydantic-ai-real-estate-listings](pydantic-ai-real-estate-listings) | Python · Pydantic AI | a suite that catches invented field values, before and after a prompt fix |
| [opik-ts-podcast-title-prompts](opik-ts-podcast-title-prompts) | TypeScript · Opik SDK | two prompt-library versions and the same suite run against each |
| [optimizer-music-genre-classifier](optimizer-music-genre-classifier) | Python · Opik Agent Optimizer | a score curve across optimizer trials, the winner saved as a prompt version |
| [dspy-astronomy-fact-check](dspy-astronomy-fact-check) | Python · DSPy | one suite, two experiments: the uncompiled program against the compiled one |

**Cost, latency and long-running work**

| Example | Stack | What you'll see in Opik |
|---|---|---|
| [litellm-recipe-adapter](litellm-recipe-adapter) | Python · LiteLLM | the same requests sent to OpenAI and Anthropic, compared on cost and latency |
| [temporal-py-film-festival-review](temporal-py-film-festival-review) | Python · Temporal | one trace spanning a client and a worker process, with a failed attempt and its retry |

**Audio, images and no-code**

| Example | Stack | What you'll see in Opik |
|---|---|---|
| [whisper-vet-voicemail-triage](whisper-vet-voicemail-triage) | Python · OpenAI TTS + transcription | playable MP3 attachments on traces, a judge tamed with runs-per-item |
| [openai-shipping-label-extraction](openai-shipping-label-extraction) | Python · OpenAI vision | label images as attachments, and a suite that honestly fails on the hardest labels |
| [n8n-food-bank-volunteers](n8n-food-bank-volunteers) | n8n (Docker) | a canvas-built workflow traced node by node with no instrumentation code |

## Running one

You need an Opik to send traces to. The examples were run against a self-hosted Opik on `localhost:5173`; Opik Cloud works too, with an API key.

1. Copy `.env.example` to `.env` at the repo root and fill in `OPENAI_API_KEY` (and `ANTHROPIC_API_KEY` for the two examples that use Claude). Every example looks for this file by walking up from its own folder.
2. `cd` into an example and follow its **Run it yourself** section. As a rule of thumb:
   - Python: `uv run main.py` (or the CLI the README names), with `uv` and Python 3.12+
   - TypeScript: `npm install && npm run demo`, with Node 20+
   - Java: `./run.sh`, with JDK 21 (the Maven wrapper is included)
   - n8n: `./setup.sh && ./demo.sh`, with Docker
3. Open the Opik project named after the folder.

Most examples finish in under a minute and cost a few cents or less with `gpt-4o-mini`.

## What's in each folder

Every example has the same shape, so after reading one you know where to look in the rest:

- **README.md**: the problem, what to open in Opik, exact run commands, experiments to try, and a **Gotchas** section of things that actually went wrong while building it.
- **.env.example**: only the variables that example reads, each with a link to where to get it.
- **the app**: kept small enough to read in one sitting. Every place it touches Opik has a short comment saying what that line produces in the UI.
- **data/** or **docs/**: fictional, offline data. Nothing calls an external API except the model provider.
- **tests/**: offline tests that run with no keys and with tracking switched off (the Java and n8n examples skip these).

The git history is part of the lesson: most examples arrive as a short series of commits, starting from the plain app and then adding tracing, then evaluation. `git log -p -- <folder>` shows exactly what changed to make an app observable.

## License

[Apache 2.0](LICENSE).

---

*Inspired by Opik's examples and documentation · [Opik on GitHub](https://github.com/comet-ml/opik) · [Opik docs](https://www.comet.com/docs/opik/)*
