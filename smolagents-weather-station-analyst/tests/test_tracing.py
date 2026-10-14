import agent
import tracing


def test_tracing_is_a_noop_when_tracking_disabled(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")
    assert tracing.setup_tracing() is None


def test_ask_runs_with_a_stub_agent_and_tracking_disabled(monkeypatch):
    monkeypatch.setenv("OPIK_TRACK_DISABLE", "true")

    class StubAgent:
        def run(self, prompt):
            assert agent.BRIEFING in prompt and prompt.endswith("Question: Which?")
            return 42

    assert agent.ask(StubAgent(), "Which?") == "42"


def test_briefing_points_at_the_csv():
    assert "readings.csv" in agent.BRIEFING
    assert len(agent.QUESTIONS) == 3
