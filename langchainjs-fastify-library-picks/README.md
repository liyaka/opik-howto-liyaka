# langchainjs-fastify-library-picks

*A library chat widget backend where every reader's conversation shows up in Opik as one clean transcript.*

![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=nodedotjs&logoColor=white)
![Fastify](https://img.shields.io/badge/fastify-5-000000?style=flat&logo=fastify&logoColor=white)
![opik-langchain](https://img.shields.io/badge/opik--langchain-2.2.100-2f54eb?style=flat)

A reader opens the chat on the Elmwood Public Library site and types "a cozy mystery near the sea". A minute later they ask "anything shorter?". Server-side, those are two unrelated `POST /chat` requests, and the second one only makes sense next to the first. If your traces are one-per-request, debugging a bad recommendation means stitching turns together by hand. This example shows how to make Opik do the stitching: one thread per reader, and a root run whose input and output are plain sentences so the transcript is readable at a glance.

## What you'll build

A Fastify server with a single `POST /chat` route in front of a LangChain.js chain. The chain takes the reader's message as a **string** and returns the recommendation as a **string**. Inside, it loads that reader's history, searches (through a LangChain retriever) a fictional 15-book catalog in `data/catalog.json` using the reader's earlier messages too (so "anything shorter?" still knows you wanted a cozy sea mystery), builds the prompt, calls `gpt-4o-mini`, and parses the reply.

Tracing is one `OpikCallbackHandler` per reader, created with `threadId` set to the reader's session id. `npm run demo` starts the server, sends three scripted readers three turns each, flushes, and exits.

## See it in Opik

Open the `langchainjs-fastify-library-picks` project. It holds 9 traces, all named `library-picks-turn`, one per reader message.

**Threads tab.** Three threads: `reader-cozy-mystery`, `reader-space-optimist` and `reader-book-club`, each with 3 turns. The first message of each reads like a sentence ("I want a cozy mystery set somewhere near the sea."), and the last is the bot's reply, because the root run takes and returns plain strings. Open a thread to read the whole conversation top to bottom.

**Traces tab.** Open any trace. The tree is `library-picks-turn` with five children: `load-session-history`, `pick-candidates` (with `search-catalog` nested inside it), `ChatPromptTemplate`, `ChatOpenAI` and `StrOutputParser`. `ChatOpenAI` is the one `llm` span: model `gpt-4o-mini`, between 231 and 407 prompt tokens in the demo run, and a non-null estimated cost of $0.000065 to $0.000089 per turn (the 9 turns total $0.00069). `search-catalog` is a `tool` span whose output lists the matched books as documents with their page counts. Open `ChatPromptTemplate` on a follow-up turn to see those matches and the earlier messages that went to the model.

## Run it yourself

1. `cd langchainjs-fastify-library-picks && npm install`
2. `cp .env.example .env` and fill in `OPENAI_API_KEY`. For a local Opik leave the defaults; for Opik Cloud set `OPIK_API_KEY`, `OPIK_WORKSPACE` and remove `OPIK_URL_OVERRIDE`.
3. `npm run demo` to play the three scripted conversations.
4. `npm run verify` to read the project back from Opik's REST API and check threads, spans, tokens and cost.
5. `npm run dev` to run the server on port 3161 and `curl -X POST localhost:3161/chat -H 'content-type: application/json' -d '{"sessionId":"me","message":"something with dragons"}'`.

Tests: `npm test` (offline; they set `OPIK_TRACK_DISABLE=true`, Opik's switch that makes the callback handler record nothing).

## Poke around

- Send two messages with different `sessionId` values: the second reader gets no memory of the first, and Opik shows two threads.
- Change the callback's `threadId` to a constant and rerun the demo: every reader collapses into one giant thread.
- Make the chain return an object instead of a string and look at the Threads tab again: the first and last message become JSON.
- Ask for something the catalog does not have ("a cookbook of volcano recipes") and open the `ChatPromptTemplate` span: the model was told there were no matches.

## Gotchas we hit

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-langchain@2.2.100`.** `opik-langchain` declares a stale peer range on `opik`. Force the current `opik` for it with an npm override in `package.json`:

```json
"overrides": { "opik-langchain": { "opik": "$opik" } }
```

**`require() of ES Module .../cookie/dist/index.js from .../light-my-request/lib/cookies.js not supported` in tests.** Fastify's `app.inject()` loads a dependency that Node 20.16 cannot `require()`. The tests here start the app with `listen({ port: 0 })` and call it with `fetch` instead.

**The catalog lookup shows up as an anonymous `general` span with a bare string output.** That is what a plain `RunnableLambda` becomes in the trace. Make the lookup a `BaseRetriever` subclass and call it with the parent step's `config` (`retriever.invoke(query, config)`): `opik-langchain` then records a `tool` span named `search-catalog` with the retrieved documents as output, nested under the turn. We checked on the pinned versions that retriever runs are recorded, not dropped.

## How it's put together

- `src/server.ts`: Fastify app, per-reader session with its own `OpikCallbackHandler`, shared Opik client and flush.
- `src/chain.ts`: the string-in, string-out chain, plus the `CatalogRetriever` that becomes the `tool` span.
- `src/catalog.ts`: catalog loading and keyword search.
- `src/demo.ts`: starts the server, plays three readers, flushes, exits.
- `src/verify.ts`: queries Opik and prints PASS/FAIL checks.
- `data/catalog.json`: the fictional catalog.
- `tests/`: catalog search, the retriever, and the chat route with a fake model and tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
