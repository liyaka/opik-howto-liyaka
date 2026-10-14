"""Run scripted multi-turn claim conversations through the claims desk."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()

from agents import Runner

from desk import triage_agent

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
        for message in turns:
            print(f"\nUser:  {message}")
            result = Runner.run_sync(triage_agent, history + [{"role": "user", "content": message}])
            print(f"Agent ({result.last_agent.name}): {result.final_output}")
            history = result.to_input_list()


if __name__ == "__main__":
    run_demo()
