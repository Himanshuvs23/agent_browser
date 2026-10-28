# Agent Browser AI Runtime

A standalone agent runtime for the Agent Browser Chromium fork. The runtime is deliberately isolated from Chromium so the graph can be tested without building the browser.

## First milestone

- Typed task state and structured plan/step records
- LangGraph workflow: context -> intent -> plan -> policy -> execute -> verify -> finalize
- Mock browser adapter (no real browser actions yet)
- FastAPI endpoint for submitting a task
- Tests for graph routing and safe mock execution

## Local setup

Requires Python 3.11+.

```bash
cd ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8765
```

Try it:

```bash
curl -X POST http://127.0.0.1:8765/tasks \
  -H 'Content-Type: application/json' \
  -d '{"request":"Summarize the current page","context":{"page_title":"Example","page_url":"https://example.com"}}'
```

This initial milestone uses deterministic planning and a mock adapter. It does not call an LLM or control Chromium yet. The next milestone will add provider configuration and model-backed planning; real browser tools will be added after the graph and approval policy are tested.
