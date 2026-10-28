"""Shared state and typed records for the agent graph."""

from typing import Any, Literal, TypedDict


Intent = Literal["question", "research", "browser_action", "multi_step", "unknown"]
StepStatus = Literal["pending", "awaiting_approval", "running", "succeeded", "failed", "skipped"]


class PlanStep(TypedDict):
    id: str
    description: str
    action: str
    status: StepStatus
    result: str | None
    error: str | None
    requires_approval: bool


class AgentState(TypedDict, total=False):
    task_id: str
    request: str
    context: dict[str, Any]
    intent: Intent
    plan: list[PlanStep]
    current_step: int
    events: list[dict[str, Any]]
    needs_approval: bool
    approval_granted: bool
    execution_result: str
    verification_passed: bool
    final_response: str
    error: str | None
