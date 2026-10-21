## Context

The existing Reflex backend makes login and service-request calls to Xano. Login currently reports a shared connection message for several distinct failure classes. Service requests already select `XANO_SERVICES_URL` when present and otherwise fall back to `XANO_API_URL`, but operators are not clearly told that the service URL should point to a separate Xano API group. The service-message helper logs `message_text`, and message handlers can log raw exception representations.

This change is planning-only with respect to Xano: the tagged endpoint already exists, and no Xano endpoint, schema, or authorization behavior is in scope.

## Goals / Non-Goals

**Goals:**

- Give login users and operators clear, safe guidance for invalid configuration, transport failure, HTTP failure, and malformed Xano responses.
- Keep passwords, tokens, full response bodies, conversation text, and untrusted exception text out of logs and user-facing diagnostics.
- Include useful endpoint and HTTP status context without emitting URL user information, query strings, or fragments.
- Make the service-group URL explicit in project setup documentation while preserving the existing fallback when that setting is absent.
- Verify behavior using deterministic tests and mocked HTTP responses.

**Non-Goals:**

- Change Xano authorization, endpoints, request payload contracts, database schema, or workspace configuration.
- Change login success routing, server-side token handling, message display, or valid request behavior.
- Remove backward-compatible fallback to `XANO_API_URL`.
- Modify the already-existing tagged Xano endpoint or its local file.

## Decisions

### Classify login failures by phase

Keep the existing backend-only login request and classify failures into:

1. **Configuration:** missing or invalid `XANO_API_URL`; do not send credentials.
2. **Transport:** DNS, connection, or timeout failures before receiving an HTTP response.
3. **HTTP:** an HTTP response with a non-success status; retain the existing safe invalid-credentials feedback for the established credential-rejection statuses, and show a distinct safe HTTP diagnostic for other statuses.
4. **Malformed response:** a successful response that is invalid JSON or lacks the fields required to establish the session or resolve the account.

For each diagnostic, provide an actionable next step (check the relevant environment variable/endpoint, network reachability, HTTP response status, or Xano response contract). Preserve valid login behavior, loading state, password clearing, role routing, and server-side token storage.

### Load local development configuration in the backend

Load the root `.env` file when `sosdrive.py` is imported, before login events read configuration. Use the existing Python dotenv ecosystem and do not override process environment values, so deployments and IDE launch configurations retain precedence. Provide a `.env.example` with placeholders and instructions to replace them with the actual API-group URL; never commit a real workspace URL or credentials.

### Sanitize diagnostic endpoint context

Build endpoint context from a parsed URL rather than logging arbitrary exception or URL strings. Permit only scheme, host/port, and the request path needed to locate the route. Remove user information, query strings, and fragments. Include the numeric HTTP status when a response exists; use an explicit transport/configuration/malformed category when there is no usable status. Never include request payloads, passwords, tokens, full response bodies, or raw exception messages in user feedback or diagnostics.

### Configure the service-group URL explicitly

Use the existing service URL selection helper. When `XANO_SERVICES_URL` is set, it is the service-group base URL and takes precedence over `XANO_API_URL`. When it is unset or blank, preserve the established fallback to `XANO_API_URL`; do not silently replace a configured value with another group. Document that `XANO_SERVICES_URL` should identify the separate Xano group that owns service-request and related service endpoints, and show both variables in setup guidance. Do not alter authorization headers or tokens.

### Redact conversation and exception data

Remove message bodies from request logs. Service-message success/failure logs may include the operation, safe endpoint context, HTTP status, and exception class/category only. Message-loading and sending handlers must not pass exception text, traceback data that can contain request/response content, or `XanoAPIError.message` into logs. Keep user-facing conversation errors generic and safe rather than incorporating exception details.

### Test through existing Python test patterns

Add unit tests using mocked requests and captured logs. Tests should assert exact diagnostic categories/messages, status and sanitized endpoint context, no credential submission for invalid configuration, service URL precedence and fallback, and absence of message text or sensitive exception content in logs. Include malformed JSON and structurally incomplete success responses. Keep all tests local; do not call the tagged Xano endpoint or require credentials.

## Risks / Trade-offs

- **[HTTP error bodies may contain sensitive or untrusted content]** → Do not log complete bodies or raw exception strings; use status and a bounded, explicitly safe field only where the current credential-rejection contract allows it.
- **[Endpoint URLs may include sensitive URL components]** → Construct display/log context from parsed and sanitized URL components and exclude user information, query, and fragment.
- **[A configured service URL can point to the wrong group]** → Document the expected service-group base URL and test that a configured value takes precedence rather than silently falling back.
- **[Older environments may not define `XANO_SERVICES_URL`]** → Keep `XANO_API_URL` fallback when the service setting is absent or blank.
- **[Message exception logging is spread across request helpers and UI state handlers]** → Cover both the low-level send helper and message load/send handlers with captured-log tests.

## Migration Plan

No data or endpoint migration is needed. Add the service-group environment variable to setup documentation and deployments that use a separate Xano group. Existing environments continue using `XANO_API_URL` until `XANO_SERVICES_URL` is configured. Rollback requires only reverting the client/documentation changes; no Xano rollback is involved.

## Verification

- Test `.env` loading and process-environment precedence; test missing and invalid `XANO_API_URL` and assert no login HTTP request is made.
- Test network exceptions, credential rejection statuses, other HTTP statuses, non-JSON success responses, and success responses missing required authentication/identity fields.
- Assert diagnostic category/message, status when available, actionable endpoint context, and redaction of URL user information, query, and fragment.
- Test `XANO_SERVICES_URL` precedence and `XANO_API_URL` fallback only when the service URL is unset or blank.
- Capture logs for successful and failed service-message operations and assert message text and raw exception details are absent while safe operation/status metadata remains.
- Run focused Python unit tests and OpenSpec validation if the CLI is available in the environment.
