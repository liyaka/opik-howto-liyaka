"""Run scripted multi-turn claim conversations through the claims desk."""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()
# The project name must be set before opik is imported; every trace lands in this project.
os.environ.setdefault("OPIK_PROJECT_NAME", "openai-agents-insurance-claims")

import opik
from agents import Runner, set_trace_processors, trace
from opik.integrations.openai.agents import OpikTracingProcessor

from desk import triage_agent

# OpikTracingProcessor replaces the SDK's default exporter: each agent run becomes an Opik trace,
# with agent, handoff, function (tool) and generation (llm) spans nested under it.
set_trace_processors([OpikTracingProcessor()])

CONVERSATIONS = {
    "auto-fender-bender": [
        "Hi, I backed into a pole and dented my bumper. Repair estimate is $2,300. Policy AUT-20417.",
        "Please go ahead and file it.",
    ],
    "home-burst-pipe": [
        "A pipe burst in our kitchen and ruined the floor, about $6,400 of damage. Policy HOM-77310.",
        "Yes, open the claim please.",
    ],
    "travel-er-visit": [
        "I ended up in an emergency room abroad, bill was $4,800. My policy is TRV-55902.",
        "File it, thanks.",
    ],
}


def run_demo() -> None:
    for name, turns in CONVERSATIONS.items():
        print(f"\n=== {name} ===")
        history: list = []
        thread_id = f"{name}-{uuid.uuid4().hex[:6]}"
        for message in turns:
            print(f"\nUser:  {message}")
            # One trace per turn. The shared group_id becomes the Opik thread id, so the Threads
            # tab shows each claim conversation as one thread; without it every turn is orphaned.
            with trace(workflow_name="Claims intake", group_id=thread_id):
                result = Runner.run_sync(
                    triage_agent, history + [{"role": "user", "content": message}]
                )
            print(f"Agent ({result.last_agent.name}): {result.final_output}")
            history = result.to_input_list()


if __name__ == "__main__":
    try:
        run_demo()
    finally:
        # Traces are sent from a background thread; flush so a short script does not exit first.
        opik.flush_tracker()
