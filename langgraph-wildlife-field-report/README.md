# langgraph-wildlife-field-report

*A planner, a researcher that loops, and a writer: one season of ranger notes in, one field report out, and one Opik trace that shows what each agent cost.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
[![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)

Multi-agent apps are hard to audit after the fact. The final report reads fine, but did the
planner ask the right questions, did the researcher find the right notes, and which of the three
agents is the one burning your budget? Without a trace you can only guess.

This example runs a small LangGraph team over a fictional reserve's field notes and traces the
whole run as a single Opik trace you can read top to bottom.

## What you'll build

A package, `field_report/`, with a CLI. The graph has three agents (all `gpt-4o-mini`):

```
planner --> researcher --+
               ^         |  unanswered questions? loop
               +---------+  all answered? --> writer --> season summary
```

- **planner** splits the request into 3 to 5 questions (structured output).
- **researcher** answers one question per pass from sections of five fictional documents in
  `data/` (ranger notes for two sectors, a sighting log, waterhole and rainfall records, a patrol
  log for Kestrel Hollow Reserve), using a small offline keyword search.
- **writer** turns the findings into a markdown season summary.

`OpikTracer` plus `track_langgraph` trace the compiled graph. The keyword search is wrapped in
`@opik.track(type="tool")` so each lookup is its own span. After the run the CLI reads the trace
back from Opik and prints tokens and dollars per agent.

## See it in Opik

Open the `langgraph-wildlife-field-report` project and click the single trace named `LangGraph`.
It has 26 spans: one top-level span per node pass, so `planner`, then five `researcher` spans
in a row, then `writer`. Under each researcher pass sit a `retrieve_notes` tool span (the query
and the sections it returned), a `ChatOpenAI` llm span with the exact prompt, completion and
token usage, and a `more_questions` span for the routing decision.

Open the graph view on the trace: the planner, researcher and writer nodes appear with the
researcher's self-loop, because `track_langgraph` stores the graph definition in the trace
metadata. The llm spans carry `total_estimated_cost`, so cost splits by agent. In the verified
run:

| agent      | passes | tokens | cost (USD) |
|------------|-------:|-------:|-----------:|
| planner    |      1 |    270 |   0.000088 |
| researcher |      5 |  1,917 |   0.000520 |
| writer     |      1 |  1,240 |   0.000386 |
| total      |        |  3,427 |   0.000993 |

The CLI prints the same table, computed from the spans stored in Opik. Each extra planner
question adds a whole researcher pass.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY` (a repo-level `.env` also works). Opik defaults
   to a local server or whatever `opik configure` set up.
2. `uv sync`
3. `uv run field-report`
4. Open the `langgraph-wildlife-field-report` project in Opik and click the trace.

## Poke around

- Pass `--request "Focus only on anti-poaching results"` and watch the planner emit fewer
  questions; the loop in the trace gets shorter and the researcher row of the table shrinks.
- Open a `retrieve_notes` span and compare its returned sources with the researcher's answer.
  When an answer says "the notes don't cover this", the span shows whether retrieval or the
  model was at fault.
- Edit a number in `data/patrol-and-poaching-log.md` and follow it through retrieval, finding and
  summary.
- Run with `--no-costs` to skip the read-back, or set `OPIK_TRACK_DISABLE=true` to run untraced.

## Gotchas we hit

**`openai.OpenAIError: Missing credentials` when importing the package in tests.**
Building `ChatOpenAI(...)` at module import needs a key, so even offline tests failed. The model
is now created lazily in `get_llm()`, which the tests monkeypatch.

**A plain Python function inside a node is invisible in the trace.**
The tracer only sees LangChain runnables, so retrieval would show nothing. Decorate it:
`@opik.track(name="retrieve_notes", type="tool")`.

## How it's put together

- `field_report/state.py` - graph state and the planner's structured output.
- `field_report/corpus.py` - loads `data/` and ranks sections by keyword weight.
- `field_report/nodes.py` - planner, researcher, router and writer.
- `field_report/graph.py` - the LangGraph wiring.
- `field_report/tracing.py` - `OpikTracer`, `track_langgraph` and flush.
- `field_report/costs.py` - per-agent token and cost roll-up from stored spans.
- `field_report/cli.py` - the `field-report` entry point.
- `data/` - five fictional documents.
- `tests/test_field_report.py` - offline tests with a stub model: search, router, graph loop,
  a traced function with tracking disabled, and the cost roll-up.
  Run `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

---

*built with Opik · inspired by Opik's examples and documentation*
