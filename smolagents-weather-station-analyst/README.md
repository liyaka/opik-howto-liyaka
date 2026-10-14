# smolagents-weather-station-analyst

*Ask a code-writing agent about sensor data, then open the trace and read the exact pandas it ran.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![smolagents](https://img.shields.io/badge/smolagents-CodeAgent-FFD21E?style=flat)
![Opik](https://img.shields.io/badge/Opik-OpenTelemetry-2f54eb?style=flat)

## The problem

Weather stations lie. A thermometer freezes on one value, a humidity probe reports 187 %, a
logger goes dark for a day and a half. If you let an LLM agent answer "is the data any good?",
it will write some pandas, run it, and hand you a number with total confidence. Whether that
number is right depends entirely on code you never saw. This example makes that code the thing
you look at.

## What you'll build

A smolagents `CodeAgent` (gpt-4o-mini) that answers three data-quality questions about
`data/readings.csv`: four fictional stations, hourly temperature, humidity, wind, pressure and
rain for 21 days of March 2026 (1,976 rows). Three faults are planted:

| Station | Fault |
|---|---|
| RIDGE-02 | temperature stuck at 14.3 C for 72 hours |
| HARBOR-03 | one impossible humidity reading, 187 %, on 2026-03-13 13:00 |
| VALLEY-04 | 40 hourly rows missing (a logger outage) |

`checks.py` computes the same facts directly with pandas, and `main.py` prints that ground
truth under each agent answer so you can see whether the agent got it right. Tracing is
OpenInference's smolagents instrumentation exporting OTLP to Opik; there are no decorators in
the agent code.

## See it in Opik

Open the `smolagents-weather-station-analyst` project. There are three traces, one per question,
each named `CodeAgent.run`, and the Input and Output columns are filled: input is the task
(briefing plus question), output is the agent's final sentence.

Open the stuck-sensor trace. It has 8 spans: the `CodeAgent.run` root, three `Step N` spans
(each with an `OpenAIModel.generate` child) and a `FinalAnswerTool` span. Two kinds of span carry the audit trail:

- `OpenAIModel.generate` output holds the model's reasoning and the pandas it wrote, for
  example a `find_consecutive_duplicates` helper built on
  `(temp_c != temp_c.shift()).cumsum()`.
- `Step 2` output holds the execution log of that code: `temp_c 14.3, consecutive 121.0,
  hours 72.0, Name: (RIDGE-02, 418)`. That is the evidence behind the answer "RIDGE-02 is
  repeating 14.3 C for 72 consecutive hours".

The `generate` spans also carry token usage (about 2,100 prompt tokens at step 1 growing to
about 3,300 by step 3, because each observation is appended to the context).

## Run it yourself

1. Start a local Opik at `http://localhost:5173` (see the Opik docs).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` one directory up also works).
3. `uv sync`
4. `uv run main.py` (takes under a minute and costs a few cents)
5. Open the project in Opik and look at the newest traces.

## Poke around

- Run it twice. The agent writes different code each time. In one of our runs it answered
  "71 consecutive hours" for the stuck sensor; the planted run is 72. The trace showed an
  off-by-one in its own run counting, which is exactly what the ground-truth line catches.
- Add a fourth station to `generate_data.py` with a pressure spike, regenerate the CSV
  (`python3 generate_data.py`) and add a question to `agent.py`.
- Ask a question the data cannot answer (for example, which station has a broken wind sensor) and
  read the steps to see how the agent copes.
- Swap `gpt-4o-mini` for another model in `agent.py` and compare the generated code per step.

## Gotchas we hit

**Cost is empty on every span.** The OTLP spans record prompt and completion tokens and the
model name, but Opik does not compute `total_estimated_cost` for them: the spans have no
recognised provider attribute. This example is about the code audit, so we leave it; the
dollar figure is something you would derive from the token counts yourself.

**The generated code is not on the `Step` span.** `Step N` has the execution log as its
output, but its input is just a stringified `ActionStep(...)` object. The pandas the model
wrote is in the output of the `OpenAIModel.generate` child. Open both to see code and result
side by side.

**Different runs, different code.** The same question can take two or three steps and produce
slightly different counting logic. Compare answers against `checks.py` rather than trusting a
single run.

## How it's put together

- `main.py` loads keys, turns on tracing, asks the three questions, prints ground truth, flushes.
- `tracing.py` sets the OTLP endpoint and headers (workspace, project) and instruments smolagents.
- `agent.py` builds the `CodeAgent`, the briefing and the three questions.
- `checks.py` loads the CSV and computes the planted faults with plain pandas.
- `generate_data.py` regenerates `data/readings.csv` deterministically.
- `tests/` holds offline tests: fault detection, ground-truth lines, a stub-agent call with
  tracking disabled (`OPIK_TRACK_DISABLE=true`).

Run the tests with `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

---

*built with Opik · inspired by Opik's examples and documentation*
