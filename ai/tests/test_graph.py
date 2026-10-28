from app.graph.builder import agent_graph


def test_graph_runs_without_browser_actions():
    result = agent_graph.invoke(
        {
            "task_id": "test-1",
            "request": "Summarize the current page",
            "context": {"page_title": "Example", "page_url": "https://example.com"},
            "events": [],
        }
    )
    assert result["verification_passed"] is True
    assert "mock mode" in result["final_response"]
    assert any(event["type"] == "policy_checked" for event in result["events"])


def test_empty_request_fails_closed():
    result = agent_graph.invoke(
        {
            "task_id": "test-2",
            "request": "",
            "context": {},
            "events": [],
        }
    )
    assert result["error"] == "Request cannot be empty."
    assert "couldn't complete" in result["final_response"]
