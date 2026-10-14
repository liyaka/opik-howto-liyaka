from types import SimpleNamespace

from field_report import costs, graph, nodes
from field_report.corpus import load_corpus, search


class FakeLLM:
    """Stands in for ChatOpenAI: canned plan, canned answers."""

    def with_structured_output(self, schema):
        return SimpleNamespace(
            invoke=lambda msgs: schema(questions=["How many elephants were logged?", "How many snares were removed?"])
        )

    def invoke(self, msgs):
        return SimpleNamespace(content="stub answer")


def test_search_ranks_the_relevant_section_first():
    hits = search("snares removed by rangers", load_corpus())
    assert hits[0]["source"] == "patrol-and-poaching-log.md"


def test_traced_tool_function_runs_with_tracking_disabled():
    # retrieve() is decorated with @opik.track; it still behaves like a plain function.
    hits = nodes.retrieve("borehole cost at Sablewood Pan")
    assert any(h["source"] == "waterholes-and-rainfall.md" for h in hits)


def test_router_loops_until_every_question_has_a_finding():
    state = {"questions": ["a", "b"], "findings": [{}]}
    assert nodes.more_questions(state) == "researcher"
    state["findings"].append({})
    assert nodes.more_questions(state) == "writer"


def test_graph_runs_planner_researcher_loop_writer(monkeypatch):
    monkeypatch.setattr(nodes, "get_llm", lambda: FakeLLM())
    out = graph.build_graph().invoke({"reserve": "Test Reserve", "brief_request": "report"})
    assert len(out["findings"]) == 2
    assert out["summary"] == "stub answer"


def span(id, name, type="general", parent=None, tokens=None, cost=None):
    usage = {"total_tokens": tokens} if tokens else None
    return SimpleNamespace(id=id, name=name, type=type, parent_span_id=parent, usage=usage, total_estimated_cost=cost)


def test_per_agent_rollup_groups_llm_spans_under_their_node():
    spans = [
        span("1", "planner"), span("2", "RunnableSequence", parent="1"),
        span("3", "ChatOpenAI", "llm", parent="2", tokens=100, cost=0.001),
        span("4", "researcher"), span("5", "ChatOpenAI", "llm", parent="4", tokens=50, cost=0.002),
        span("6", "researcher"), span("7", "ChatOpenAI", "llm", parent="6", tokens=70, cost=0.003),
    ]
    rows = costs.per_agent(spans)
    assert rows["researcher"] == {"passes": 2, "tokens": 120, "cost": 0.005}
    assert rows["planner"]["tokens"] == 100 and rows["writer"]["passes"] == 0
    assert "total" in costs.format_table(rows)
