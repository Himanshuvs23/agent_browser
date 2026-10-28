# AO Browser Agent Contract (Draft)

Status: design contract for review; not a generated Mojo schema and not a stable public API.

## Design rules

1. All messages are typed and versionable.
2. Page content and model output are untrusted.
3. The model proposes actions; browser-side policy decides whether an action is allowed.
4. Approval is associated with one immutable pending action.
5. Secrets never appear in task state, UI messages, prompts, or logs.
6. All text and lists have explicit size limits in the implementation.

## Task lifecycle

- `created`
- `collecting_context`
- `planning`
- `awaiting_approval`
- `executing`
- `verifying`
- `completed`
- `failed`
- `cancelled`

Terminal states are `completed`, `failed`, and `cancelled`. A cancelled task must not start additional tools.

## UI-to-browser requests

### SubmitTask
- `request_id`: unique request identifier.
- `user_prompt`: user-authored task, length-limited.
- `context_options`: explicit options such as whether selected text may be included.
- `active_tab_id`: browser-derived tab identity; never trust a tab ID supplied by arbitrary page JavaScript.

### CancelTask
- `task_id`: task to cancel.

### ResolveApproval
- `task_id`: task awaiting approval.
- `approval_id`: one-time identifier for the exact pending action.
- `decision`: approve or reject.

The browser must verify that the task is still awaiting this exact approval and that the target context has not changed. The UI must not be able to approve an action merely by submitting a guessed ID.

## Browser-to-UI events

### TaskUpdated
- `task_id`
- `state`
- `human_readable_status`
- `step_index` and `step_count`, when applicable

### ApprovalRequested
- `task_id`
- `approval_id`
- `action_summary`
- `target_origin`
- `risk_explanation)
- `expires_at` or equivalent browser-side expiry policy

### TaskFinished
- `task_id`
- `status`
- `result_text`
- `error_code`, when failed

No event should contain credentials, cookies, authorization headers, or unrelated browsing data.

## Planned tool envelope

Every proposed tool call should have:
- `tool_call_id`
- `tool_name` from a compile-time allow-list
- `arguments` parsed into that tool's typed schema
- `risk_level`
- `requires_approval`
- `expected_tab_id` and expected origin where relevant

Reject unknown tools, unexpected fields, oversized strings, invalid URLs, and malformed arguments. Never dispatch arbitrary model-provided code.

## Provider abstraction

Provider configuration should include a provider ID, endpoint policy, model ID, and credential reference. A credential reference points to secure platform storage; it is not the raw key. Provider adapters must enforce HTTPS, timeouts, response limits, cancellation, and redacted error reporting.

## Data minimization

The default context is active-tab title and URL. Page text, selection, or accessibility data should be requested only when needed, bounded in size, and disclosed as data that may be sent to the configured provider. Do not gather cookies, passwords, payment details, or unrelated tabs as agent context.

## Open implementation questions

- Which side-panel integration API is available in the exact Chromium revision in this fork?
- Which existing WebUI registration and Mojo patterns should be followed?
- Which Chromium credential-storage and network abstractions are appropriate for the target platform?
- What exact tool set should ship in the first build?
- How should users configure local-compatible endpoints while preserving secure defaults?
