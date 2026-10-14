# ollama-beekeeping-rag

*A RAG assistant for a beekeeping handbook that never calls a cloud model, and still shows every step in Opik.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![langchain-ollama](https://img.shields.io/badge/langchain--ollama-1.1-1C3C3C?style=flat)
![Model](https://img.shields.io/badge/model-llama3.2%3A1b-grey?style=flat&logo=ollama&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.2-2f54eb?style=flat)](https://github.com/comet-ml/opik)

## The problem

Running models locally removes the API bill and the data-leaves-the-building worry, but it also removes the dashboards that usually come with a provider. A one-billion-parameter model also gets things wrong far more often than a hosted one, so when an answer is off you need to know whether retrieval or generation was at fault. This example runs a complete RAG loop on your machine, with no cloud LLM and no provider key, and traces it with Opik so that question can be answered with one click.

## What you'll build

An assistant over the handbook of Larkspur Hollow, a fictional apiary: five short documents in `docs/` covering hive inspections, swarm prevention, the varroa treatment calendar, honey harvest and winter preparation. `nomic-embed-text` embeds the 19 handbook sections into an in-memory vector store, and `llama3.2:1b` answers from the two best-matching sections. Both models run in your local Ollama. `main.py` asks three questions; each one becomes one trace via Opik's `OpikTracer`.

## See it in Opik

Open the `ollama-beekeeping-rag` project (local Opik: http://localhost:5173). The Traces tab lists three traces named `ask_the_handbook`, tagged `ollama`, `rag`, `local`. Open one and expand the tree:

- an `llm` span named `ChatOllama` holding the full prompt and the answer, with `ls_provider: ollama` and `ls_model_name: llama3.2:1b` in its metadata;
- a `tool` span named `search_handbook` whose output is the two handbook sections that were retrieved (our own `@opik.track` span), nested inside a `general` span of the same name that LangChain created for the wrapping step;
- `general` spans for the prompt, parser and passthrough steps.

Compare the last trace, "How much honey must I leave the colony for winter?". The `search_handbook` output contains the "Leaving enough" section with the 20 kg rule, yet the model answered "The handbook does not cover this question." Retrieval did its job and the 1B model ignored its context, so the fix is the prompt or a bigger model, not the chunking. In the other two traces the retrieved sections match the questions, though the model still garbles the first answer (it says "inspect hives 7 times" instead of every seven days).

The `ChatOllama` spans carry no token counts and no cost; see Gotchas.

## Run it yourself

1. Install [Ollama](https://ollama.com/download), start it, and pull the models: `ollama pull llama3.2:1b && ollama pull nomic-embed-text`.
2. Have Opik reachable: run `opik configure` for Opik Cloud, or point at a self-hosted instance with `OPIK_URL_OVERRIDE` (see `.env.example`). No provider key is needed.
3. `uv sync`
4. `uv run main.py` (CPU inference: expect a minute or two)
5. Open the `ollama-beekeeping-rag` project in Opik.

Offline tests (no Ollama, no keys, tracing disabled): `OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Ask something the handbook lacks ("How do I extract wax?") and see which sections the `search_handbook` span returns and whether the model admits the gap.
- Change `k` in `rag.build_chain` from 2 to 4 and compare prompt size and answer quality on the honey question.
- Swap `CHAT_MODEL` in `rag.py` for a larger model you have pulled and compare the same three traces.
- Edit a number in `docs/winter-prep.md` and confirm the answer and the retrieved section change together.

## Gotchas we hit

**`ImportError: cosine_similarity requires numpy to be installed`.** `InMemoryVectorStore` computes similarity with numpy but `langchain-core` does not depend on it. Add `numpy` to your dependencies (it is in `pyproject.toml` here).

**The retrieval step is missing from the trace.** With a bare retriever in the chain (`{"context": retriever | format, ...}`), the trace on these versions (opik 2.2.100, langchain-core 1.6) showed the prompt, parser and lambda spans but no retriever span, so you could not see what was fetched. Wrap retrieval in a function decorated with `@opik.track(name="search_handbook", type="tool")` and put that function in the chain; its span shows the question and the fetched sections.

**Token usage and cost are empty on `ChatOllama` spans.** `langchain-ollama` responses are not mapped to Opik usage, so `usage` is null and no cost is estimated. That is expected for a local model; the value here is the prompt, output and latency, not spend.

## How it's put together

- `rag.py`: loads and chunks `docs/`, builds the tracked `search_handbook` function and the LangChain chain.
- `main.py`: checks Ollama and its models, runs three questions under `OpikTracer`, flushes.
- `docs/`: the five fictional handbook documents.
- `tests/`: offline tests with a keyword embedder and a fake chat model, including a call to the traced function with tracking disabled; `conftest.py` disables tracing.
- `.env.example`: Ollama URL and optional Opik settings; no provider key.

---

*built with Opik · inspired by Opik's examples and documentation*
