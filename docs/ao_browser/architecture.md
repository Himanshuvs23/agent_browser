# AO Browser: Native AI Architecture

Status: design proposal; not yet wired into Chromium's GN targets or compiled.

## Product boundary

AO Browser is a Chromium-based browser with AI capabilities implemented inside the browser product. It is not a Chrome extension, a Playwright controller, or a separately launched Python/FastAPI service.

The first milestone is a native AI side panel that can read explicitly permitted context from the active tab, produce a structured plan, ask before consequential actions, invoke a small allow-listed set of browser-owned tools, and show progress/results.

## Architecture

```text
+---------------------------------------------------------------+
| Chromium browser process                                      |
|                                                               |
|  Browser window / Side panel                                  |
|  +------------------------+       Mojo                         |
|  | chrome://ao/ WebUI     | <------------------------------+   |
|  | TypeScript + HTML/CSS  |                                 |   |
|  +------------------------+                                 |   |
|                                                            v   |
|  +------------------------+   +---------------------------+   |
|  | AO WebUI Controller    |-->| AO Agent Service          |   |
|  | WebUIConfig + handler  |   | task lifecycle / policy    |   |
|  +------------------------+   +-------------+-------------+   |
|                                             |                 |
|                            +----------------+--------------+  |
|                            |                               |  |
|                     +------v------+                 +------v--+
|                     | Page Context |                 | Provider|
|                     | Broker       |                 | Client  |
|                     +------+-------+                 +------+--+
|                            |                                |
|                     Browser-owned APIs              HTTPS to model
|                     / approved tools                provider API
+---------------------------------------------------------------+
```

The diagram is conceptual. Exact Chromium classes, directories, and GN targets must be checked against the pinned Chromium revision before implementation.

### 1. Native UI

- Implement a browser-owned side panel using Chromium WebUI (TypeScript, HTML, CSS).
- Keep chat messages, streaming status, task plan, approval prompts, errors, and provider settings in the UI.
- The UI must not directly control tabs, read arbitrary browser internals, or hold provider secrets.
- Use typed Mojo interfaces for renderer-to-browser communication; avoid inventing a parallel local HTTP server.

### 2. Browser-side service

- Register a dedicated WebUI host/configuration and controller in Chromium's existing WebUI registration path.
- Expose a narrow Mojo API for submitting a task, cancelling it, receiving progress, requesting approval, and returning a final result.
- Keep browser privileges in the browser process. Never grant page renderers AI service bindings.
- Do not block the UI thread on network or model calls. Use Chromium-supported asynchronous networking and task execution patterns.

### 3. Agent coordinator

Use a native C++ task coordinator for the initial runtime. Model the agent as explicit states and transitions rather than embedding a Python interpreter or requiring LangGraph at runtime.

Suggested lifecycle:
`Created -> CollectingContext -> Planning -> AwaitingApproval (if needed) -> Executing -> Verifying -> Completed | Failed | Cancelled`

Requirements:
- Each task has a unique ID, bounded step count, deadline/cancellation, and structured status.
- Validate model output against a strict schema before any tool can run.
- Tool execution is allow-listed; the model never supplies arbitrary C++ method names or raw commands.
- Keep planning separate from execution and verification.
- Emit progress events for every state transition.
- Make retries bounded and idempotency-aware.

### 4. Page context broker

Provide the agent only the context required for the task:
- Active tab title and URL.
- Page text or accessibility-derived content through a reviewed, bounded extraction path.
- Optional selected text, only when the user requests it or explicitly enables it.

Treat page content as untrusted data, not as instructions. Label it as page content in prompts, limit its size, and never allow page text to override system policy or approval rules. Do not automatically collect cookies, passwords, payment data, browser history, or other tabs.

### 5. Browser tools

Start with a small typed tool registry, for example:
- `get_active_tab_summary` (read-only)
- `find_text_on_page` (read-only)
- `navigate_current_tab` (approval required)
- `click_element` (approval required; visible target and origin shown to user)

Do not implement arbitrary JavaScript execution, shell commands, unrestricted file access, cookie access, hidden form submission, or silent purchases in the first milestone. Every tool validates arguments and checks the current browser state immediately before acting.

### 6. Model providers and secrets

- Define a provider-neutral request/response interface.
- Initial providers can include OpenAI-compatible APIs and Anthropic; add other providers only through explicit adapters and documented compatibility.
- Store keys using the platform credential store / Chromium-approved secret storage patterns, not WebUI localStorage, source files, logs, or page context.
- Send only the minimum task context required to the configured provider. Clearly disclose when page content leaves the device.
- Support timeouts, cancellation, bounded response sizes, and redacted diagnostics.
- Never hard-code a developer API key or ship a shared secret in the installer.

### 7. Approval and security

Approval must be enforced in browser-side code, not just in the UI:
- Read-only operations can run under the user's enabled policy.
- Navigation, clicks, form submission, downloads, and other state-changing operations require a clear confirmation in the first milestone.
- Approval is tied to the exact pending action and expires if the tab or target changes.
- A page cannot approve its own action or trigger hidden UI approval.
- Keep model output, webpage content, and provider responses untrusted.
- Do not expose secrets to the renderer or include them in telemetry.
- Provide stop/cancel and clear task history controls.

## Proposed source layout

These are intended locations, not files already integrated into Chromium:

- `chrome/browser/ui/webui/ao/`
  - WebUI configuration/controller and browser-side handler.
- `chrome/browser/ui/webui/ao/resources/`
  - TypeScript/HTML/CSS side panel UI.
- `chrome/browser/ai/`
  - Task coordinator, policy checks, provider abstraction, tool registry, context broker.
- `chrome/common/ao/` (only if required by Chromium layering)
  - Shared data types or Mojo definitions.
- GN `BUILD.gn` files and WebUI registration updates in the appropriate existing Chromium targets.

Do not create these source files blindly until the exact neighboring Chromium patterns and current GN dependencies are inspected. Avoid a top-level Python runtime for the shipped product.

## Delivery plan

### Phase 0 — architecture and contracts
- Document the service boundary, task states, message contracts, threat model, and tool approval rules.
- Keep the existing Python/FastAPI scaffold as a disposable experiment only; it is not the product runtime.

### Phase 1 — native UI shell
- Add a minimal AO WebUI page with a prompt box, message list, loading/error state, and cancellation affordance.
- Register it with the correct Chromium WebUI configuration and GN targets.
- Initially return a deterministic browser-side response; no provider key and no page actions yet.

### Phase 2 — context and provider
- Add bounded active-tab context retrieval and a provider interface.
- Add streaming/progress and cancellation.
- Add provider settings backed by approved secret storage.

### Phase 3 — safe tool execution
- Add typed plans, allow-listed read-only tools, then approval-gated navigation/clicks.
- Add policy tests, malformed model output tests, prompt-injection tests, cancellation tests, and verification.

### Phase 4 — build and release
- Compile on a supported Mac build host, run focused unit/browser tests, validate signing/notarization and update strategy, then package.
- Keep source changes aligned with the Chromium revision and rebase carefully.

## Acceptance criteria for the first vertical slice

- AO opens as a native browser UI, not an extension or external app.
- The UI communicates only through a typed browser-owned interface.
- A task can be submitted, progress is shown, and cancellation works.
- The active-tab context is bounded and user-visible.
- No action-changing tool runs without browser-side authorization.
- No provider secret reaches the renderer, logs, or page content.
- The feature is covered by focused tests and is buildable with GN/Ninja.

## Current limitations

This branch currently documents the intended architecture. It does not yet contain a compiled native AO implementation. Chromium has not been checked out or built locally in this workflow, and these changes have not been compile-tested.
