"""Initial deterministic nodes. LLM planning and real browser tools are future milestones."""

from __future__ import annotations

from app.browser.adapter import MockBrowserAdapter
from app.graph.state import AgentState, PlanStep

_browser_adapter = MockBrowserAdapter()


def load_context(state: AgentState) -> dict:
    context = state.get("context", {})
    return {
        "context": context,
        "events": state.get("events", []) + [{"type": "context_loaded"}],
    }


def classify_intent(state: AgentState) -> dict:
    request = state.get("request", "").lower()
    action_words = ("click", "type", "fill", "navigate", "open ", "scroll", "submit")
    research_words = ("research", "compare", "find sources", "investigate")
    if any(word in request for word in action_words):
        intent = "browser_action"
    elif any(word in request for word in research_words):
        intent = "research"
    elif any(word in request for word in ("steps", "then", "and after", "workflow")):
        intent = "multi_step"
    elif request.strip():
        intent = "question"
    else:
        intent = "unknown"
    return {
        "intent": intent,
        "events": state.get("events", []) + [{"type": "intent_classified", "intent": intent}],
    }


def plan_task(state: AgentState) -> dict:
    """Create a safe placeholder plan; this node will become model-backed later."""
    request = state.get("request", "").strip()
    if not request:
        return {"plan": [], "current_step": 0, "error": "Request cannot be empty."}

    # No real browser action is allowed in the initial milestone.
    step: PlanStep = {
        "id": "step-1",
        "description": f"Analyze the request: {request}",
        "action": "analyze_request",
        "status": "pending",
        "result": None,
        "error": None,
        "requires_approval": False,
    }
    return {
        "plan": [step],
        "current_step": 0,
        "events": state.get("events", []) + [{"type": "plan_created", "step_count": 1}],
    }


def check_policy(state: AgentState) -> dict:
    """Fail closed for action types not supported by the mock adapter."""
    plan = state.get("plan", [])
    if not plan:
        return {"needs_approval": False, "error": state.get("error") or "No plan was created."}
    unsupported = [step for step in plan if step["action"] != "analyze_request"]
    if unsupported:
        return {
            "needs_approval": True,
            "events": state.get("events", [])
            + [{"type": "policy_blocked", "reason": "unsupported_action"}],
        }
    return {
        "needs_approval": False,
        "events": state.get("events", []) + [{"type": "policy_checked", "allowed": True}],
    }


def execute_step(state: AgentState) -> dict:
    """Execute through the adapter boundary; the default adapter is a harmless mock."""
    plan = state.get("plan", [])
    if not plan:
        return {"execution_result": "", "error": state.get("error") or "Nothing to execute."}
    step = plan[state.get("current_step", 0)]
    if step["action"] != "analyze_request":
        return {"execution_result": "", "error": "Action is not supported by the mock adapter."}

    result = _browser_adapter.analyze_request(
        request=state.get("request", ""),
        context=state.get("context", {}),
    )
    return {
        "execution_result": result,
        "events": state.get("events", [])
        + [{"type": "step_executed", "step_id": step["id"], "mock": True}],
    }


def verify_result(state: AgentState) -> dict:
    result = state.get("execution_result", "")
    passed = bool(result) and not state.get("error")
    return {
        "verification_passed": passed,
        "events": state.get("events", []) + [{"type": "result_verified", "passed": passed}],
    }


def finalize_response(state: AgentState) -> dict:
    if state.get("error"):
        response = f"I couldn't complete this task: {state['error']}"
    elif state.get("needs_approval"):
        response = "This plan requires an approval flow or a supported browser adapter before it can run."
    elif state.get("verification_passed"):
        response = (
            "The agent graph ran successfully in mock mode. No browser actions were performed.\n\n"
            + state.get("execution_result", "")
        )
    else:
        response = "The task did not pass verification. No browser actions were performed."
    return {
        "final_response": response,
        "events": state.get("events", []) + [{"type": "task_finished"}],
    }
