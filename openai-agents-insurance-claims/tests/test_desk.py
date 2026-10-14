import asyncio
import json

from agents.tool_context import ToolContext

import desk


def test_triage_can_hand_off_to_three_specialists():
    assert [a.name for a in desk.triage_agent.handoffs] == [
        "Auto Claims Agent", "Home Claims Agent", "Travel Medical Agent"]


def test_function_tool_runs_with_tracking_disabled():
    # The Agents SDK tool wrapper is what OpikTracingProcessor records as a tool span;
    # with OPIK_TRACK_DISABLE=true it still behaves like a plain function.
    args = json.dumps({"policy_number": "TRV-55902"})
    ctx = ToolContext(context=None, tool_name="lookup_policy", tool_call_id="t1", tool_arguments=args)
    out = asyncio.run(desk.lookup_policy.on_invoke_tool(ctx, args))
    assert json.loads(out)["kind"] == "travel_medical"
