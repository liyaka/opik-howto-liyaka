"""Wire the agents into a graph: planner -> researcher loop -> writer."""

from langgraph.graph import END, START, StateGraph

from .nodes import more_questions, planner, researcher, writer
from .state import TeamState


def build_graph():
    graph = StateGraph(TeamState)
    graph.add_node("planner", planner)
    graph.add_node("researcher", researcher)
    graph.add_node("writer", writer)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_conditional_edges(
        "researcher", more_questions, {"researcher": "researcher", "writer": "writer"}
    )
    graph.add_edge("writer", END)
    return graph.compile()
