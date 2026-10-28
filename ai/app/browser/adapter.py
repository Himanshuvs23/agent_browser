"""Browser action boundary. The first implementation is intentionally a mock."""

from typing import Protocol


class BrowserAdapter(Protocol):
    """Narrow interface the agent runtime can use without knowing Chromium internals."""

    def analyze_request(
        self,
        request: str,
        context: dict,
    ) -> str:
        """Return a safe result based only on supplied context; do not control the OS."""
        ...


class MockBrowserAdapter:
    """Deterministic adapter used until the native Chromium bridge exists."""

    def analyze_request(self, request: str, context: dict) -> str:
        page_title = context.get("page_title")
        page_url = context.get("page_url")
        page_context = (
            f" Context supplied for page '{page_title}' ({page_url})."
            if page_title or page_url
            else " No browser page context was supplied."
        )
        return f"Request received: {request}.{page_context}"
