"""Local HTTP API for the standalone agent graph."""

from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.graph.builder import agent_graph

app = FastAPI(title="Agent Browser AI Runtime", version="0.1.0")


class TaskRequest(BaseModel):
    request: str = Field(min_length=1, max_length=10_000)
    context: dict = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str
    intent: str
    plan: list[dict]
    events: list[dict]
    response: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskRequest) -> TaskResponse:
    task_id = str(uuid4())
    result = agent_graph.invoke(
        {
            "task_id": task_id,
            "request": payload.request,
            "context": payload.context,
            "events": [],
            "approval_granted": False,
        }
    )
    return TaskResponse(
        task_id=task_id,
        intent=result.get("intent", "unknown"),
        plan=result.get("plan", []),
        events=result.get("events", []),
        response=result.get("final_response", "No response was generated."),
    )
