"""The claims desk: one triage agent that hands off to three specialist agents."""

import json

from agents import Agent, function_tool

import tools

MODEL = "gpt-4o-mini"


@function_tool
def lookup_policy(policy_number: str) -> str:
    """Look up a policy by number: holder, line of business, whether it is active, coverage types."""
    return json.dumps(tools.lookup_policy(policy_number))


@function_tool
def check_coverage(policy_number: str, incident_type: str, amount_usd: float) -> str:
    """Check whether an incident type is covered and estimate the payout for a given loss amount."""
    return json.dumps(tools.check_coverage(policy_number, incident_type, amount_usd))


@function_tool
def open_claim(policy_number: str, incident_type: str, amount_usd: float, summary: str) -> str:
    """Open a claim. Only call this after check_coverage says the incident is covered."""
    return json.dumps(tools.open_claim(policy_number, incident_type, amount_usd, summary))


def _specialist(name: str, line: str, incident_types: str) -> Agent:
    return Agent(
        name=name,
        handoff_description=f"Handles {line} claims.",
        instructions=(
            f"You handle {line} claims. Ask for the policy number if you do not have it. "
            "Call lookup_policy, then check_coverage for the incident (valid incident types for "
            f"this line: {incident_types}). Open a claim with open_claim only when the policyholder "
            "asks to file and coverage is confirmed. Quote the claim id. Keep replies under 80 words."
        ),
        model=MODEL,
        tools=[lookup_policy, check_coverage, open_claim],
    )


auto_agent = _specialist("Auto Claims Agent", "auto", "collision, glass, theft")
home_agent = _specialist("Home Claims Agent", "home", "water_damage, fire, theft")
travel_agent = _specialist("Travel Medical Agent", "travel medical", "emergency_care, trip_cancellation")

triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "You are the intake desk of an insurance company. Work out whether the loss is auto, home "
        "or travel medical and hand off to the matching specialist right away. Do not answer "
        "claim questions yourself."
    ),
    model=MODEL,
    handoffs=[auto_agent, home_agent, travel_agent],
)
