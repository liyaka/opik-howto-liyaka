"""A smolagents CodeAgent that audits a weather-station CSV by writing pandas code."""

from smolagents import CodeAgent, OpenAIServerModel

from checks import CSV_PATH

BRIEFING = f"""\
You are a data analyst for the Fenmoor Weather Network.
Hourly readings from four stations (March 2026) are in the CSV file at: {CSV_PATH}

Columns: station, timestamp (YYYY-MM-DD HH:MM), temp_c, humidity_pct,
wind_kph, pressure_hpa, rain_mm.

Load it with pandas and answer using concrete values from the data. Sensors
can be faulty, so check the data quality before trusting any number.
Give your final answer as one or two plain sentences, not a raw Python object.
"""

QUESTIONS = [
    "One station's temperature sensor looks frozen. Which station, what value "
    "is it repeating, and for how many consecutive hours?",
    "Is there any physically impossible humidity reading? Give the station, "
    "the timestamp and the value.",
    "Does any station have missing data? Count the hourly rows each station "
    "has and say which one has a gap and how many hours are missing.",
]


def build_agent() -> CodeAgent:
    # A CodeAgent answers by writing Python; pandas is the only import it is
    # authorised to use beyond smolagents' safe defaults.
    return CodeAgent(
        tools=[],
        model=OpenAIServerModel(model_id="gpt-4o-mini"),
        additional_authorized_imports=["pandas"],
        max_steps=6,
    )


def ask(agent: CodeAgent, question: str) -> str:
    return str(agent.run(BRIEFING + "\nQuestion: " + question))
