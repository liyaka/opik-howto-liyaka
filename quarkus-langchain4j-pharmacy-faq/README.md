# quarkus-langchain4j-pharmacy-faq

*A pharmacy medication FAQ bot on Quarkus and LangChain4j, whose prompts, retrieved leaflet sections and answers all show up in Opik over plain OpenTelemetry.*

![Java 21](https://img.shields.io/badge/java-21-ED8B00?style=flat&logo=openjdk&logoColor=white)
![Quarkus 3.40](https://img.shields.io/badge/quarkus-3.40-4695EB?style=flat&logo=quarkus&logoColor=white)
![LangChain4j](https://img.shields.io/badge/quarkus--langchain4j-1.13-1C3C3C?style=flat)
[![Opik](https://img.shields.io/badge/Opik-OTLP-2f54eb?style=flat)](https://github.com/comet-ml/opik)

Java services have no Opik SDK to lean on, and that is fine: Quarkus speaks OpenTelemetry and Opik accepts OTLP. The catch is what arrives. Out of the box the chat spans show the model and token counts, but the prompt and the completion are left off, and the vector search that fed the model is not a span at all. For a medication FAQ that is the worst gap: when an answer sounds wrong you need to see which leaflet sections the model was handed and what it was actually told. This project closes both gaps with two properties and one small wrapper class.

## What you'll build

A Quarkus service with one endpoint, `GET /ask?q=...`. At startup it reads five fictional leaflets from `docs/` (Veltrazine, Corbexol, Nuvelin, Dormaxin, Glycavora; each with dosing, interactions, storage and side effects), splits them into one chunk per section (20 chunks) and embeds them with `text-embedding-3-small` into LangChain4j's in-memory store. Each question retrieves the three closest chunks and a `@RegisterAiService` interface answers with `gpt-4o-mini`. Its system prompt keeps the bot to the leaflet text, forbids diagnosing or changing doses, and makes every answer end with an "ask your pharmacist or prescriber" sentence.

Tracing is the `quarkus-opentelemetry` extension plus properties in `application.properties`; there is no Opik dependency. `run.sh` builds the app, starts it on port 3291, asks five scripted questions (one about a drug that is not in the corpus), then stops it with SIGTERM so the exporter flushes.

## See it in Opik

Open the `quarkus-langchain4j-pharmacy-faq` project. The Traces table has five rows named `pharmacy_faq_ask`, and their Input and Output columns hold the question and the bot's answer (`{"question": "How much Nuvelin can I take in a day?"}` and the reply). Open one and expand the tree:

- `pharmacy_faq_ask` is the root, created by `FaqResource`.
- `langchain4j.aiservices.PharmacyAssistant.answer` is the AI-service call Quarkus emits.
- `retrieve_leaflet_sections` is a **tool** span from the wrapper in `TracedContentRetriever`. Its Input is the query and `top_k: 3`; its Output lists the three chunks with file, section and similarity score. For the Nuvelin question: `nuvelin.md` Dosing (0.85), Storage (0.81), Side effects (0.79).
- `completion gpt-4o-mini` is the **llm** span. Its Input holds the full prompt as sent, with the system text, the question and the three leaflet excerpts under "Answer using the following information"; its Output is the completion. The same span has model `gpt-4o-mini-2024-07-18`, provider `openai`, and usage (301 prompt + 79 completion = 380 tokens for that question) with an estimated cost of about $0.00009.

Across the five questions an answer costs between $0.00006 and $0.00009. The "Zentorin" question is the instructive one: the drug is not in any leaflet, yet retrieval still returns three chunks (Veltrazine and Corbexol interactions, scores around 0.7). The span shows why the bot is being asked to say "I do not have information" rather than improvise.

## Run it yourself

1. Have Java 21 and a running Opik (the defaults point at `http://localhost:5173`). No Maven install is needed; `mvnw` is included.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` one directory up works too).
3. `./run.sh` builds, starts the service, asks the five questions, prints the answers and exits. It takes about 30 seconds including the build, and costs well under a cent.
4. Open the project in Opik as described above.
5. To keep the service running instead: `./mvnw package -DskipTests && java -jar target/quarkus-app/quarkus-run.jar`, then `curl --get --data-urlencode "q=How should I store Glycavora?" localhost:3291/ask`.

To send traces to Comet cloud instead of a local Opik, set `OPIK_OTEL_ENDPOINT=https://www.comet.com/opik/api/v1/private/otel` and add an `Authorization` entry to `quarkus.otel.exporter.otlp.traces.headers`.

## Poke around

- Set `quarkus.langchain4j.tracing.include-prompt` and `include-completion` to `false` and rerun. The llm span keeps its model, tokens and cost, but its Input and Output lose the prompt and completion text.
- Ask `Can I take Zentorin for my headaches?` and look at the retrieval span: three chunks arrive anyway, scoring about 0.7. Raise `minScore` in `LeafletRetrievalAugmentor` to see how a threshold changes what the model is handed.
- Change `TOP_K` in `LeafletRetrievalAugmentor`. The span's `top_k` and the number of documents in its Output follow it.
- In the Traces table filter spans by type `tool` or sort by cost to find the retrieval steps and the most expensive answers.

## Gotchas we hit

**The llm span has model and tokens but empty Input and Output.** Quarkus LangChain4j leaves prompt and completion text off the spans by default. Set both of these:
```
quarkus.langchain4j.tracing.include-prompt=true
quarkus.langchain4j.tracing.include-completion=true
```
They put `gen_ai.prompt` and `gen_ai.completion` on the llm span, which Opik maps to Input and Output. Mind that the text can contain whatever users type, so think before enabling them in production.

**Nothing arrives and the log shows no error; the project never appears.** Quarkus appends `/v1/traces` to `quarkus.otel.exporter.otlp.traces.endpoint` itself. Putting the full `.../otel/v1/traces` URL there posts to `/v1/traces/v1/traces`. Use the base `http://localhost:5173/api/v1/private/otel`, with `quarkus.otel.exporter.otlp.traces.protocol=http/protobuf`.

**Every trace is called `GET /ask` and the Input column is a pile of HTTP attributes.** Opik takes the trace name and Input from the root span, which is Quarkus's HTTP server span. Set `quarkus.otel.instrument.vertx-http=false` (this also removes the outgoing `POST /chat/completions` noise), open your own root span, and put `input` and `output` attributes on it as JSON strings; Opik maps those to the trace columns.

**There is no span for retrieval.** The extension traces the AI-service call and the chat model but not the vector search. Wrap the `ContentRetriever` and record the query and results on a span, as `TracedContentRetriever` does with `gen_ai.tool.call.arguments` / `gen_ai.tool.call.result`, which Opik shows as a tool span's Input and Output.

A note on cost: the usage and dollar figure arrive on the llm span here because Quarkus sets the provider (`openai`) next to the model. If you point the service at a custom or proxied model where the provider attribute is missing, tokens still land but Opik cannot derive a cost until you add `gen_ai.system` yourself.

## How it's put together

- `pom.xml` - Quarkus 3.40 and quarkus-langchain4j (OpenAI), plus `quarkus-opentelemetry`. Pinned by the Quarkus platform BOMs.
- `src/main/resources/application.properties` - models, port, the content-on switches, the OTLP endpoint and headers.
- `docs/` - the five fictional leaflets.
- `PharmacyAssistant.java` - the AI service and its system prompt with the pharmacist disclaimer.
- `LeafletIndex.java` - splits leaflets into section chunks and embeds them at startup.
- `LeafletRetrievalAugmentor.java` - top-3 retrieval wired into the AI service.
- `TracedContentRetriever.java` - the retrieval span.
- `FaqResource.java` - the endpoint and the root span carrying the trace Input and Output.
- `Json.java` - small JSON helper for span attributes.
- `run.sh` - build, start, ask five questions, stop. There are no unit tests in this example; the run itself is the check.

---

*built with Opik · inspired by Opik's examples and documentation*
