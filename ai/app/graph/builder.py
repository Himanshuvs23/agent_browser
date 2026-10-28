"""Build the initial agent graph."""

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    check_policy,
    classify_intent,
    execute_step,
    finalize_response,
    load_context,
    plan_task,
    verify_result,
)
from app.graph.state import AgentState


def route_after_policy(state: AgentState) -> str:
    if state.get("error") or state.get("needs_approval"):
        return "finalize_response"
    return "execute_step"


def route_after_verification(state: AgentState) -> str:
    return "finalize_response"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("load_context", load_context)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("plan_task", plan_task)
    graph.add_node("check_policy", check_policy)
    graph.add_node("execute_step", execute_step)
    graph.add_node("verify_result", verify_result)
    graph.add_node("finalize_response", finalize_response)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "classify_intent")
    graph.add_edge("classify_intent", "plan_task")
    graph.add_edge("plan_task", "check_policy")
    graph.add_conditional_edges(
        "check_policy",
        route_after_policy,
        {"execute_step": "execute_step", "finalize_response": "finalize_response"},
    )
    graph.add_edge("execute_step", "verify_result")
    graph.add_conditional_edges(
        "verify_result",
        route_after_verification,
        {"finalize_response": "finalize_response"},
    )
    graph.add_edge("finalize_response", END)
    return graph.compile()


agent_graph = build_graph()
