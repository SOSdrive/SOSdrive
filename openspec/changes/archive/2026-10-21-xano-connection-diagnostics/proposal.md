## Why

The current login flow maps configuration, network, HTTP, and malformed-response failures to the same generic Xano connection message, which makes setup problems difficult to diagnose. Service-group requests can use `XANO_SERVICES_URL`, but the setting and its fallback to `XANO_API_URL` are not clearly documented. Message sending and related exception paths also log conversation content or raw exception details that may contain private message data.

## What Changes

- Make server-side login diagnostics actionable for configuration, network, HTTP, and malformed-response failures while keeping passwords, tokens, response bodies, and exception text out of user-visible errors and logs.
- Load project-local `.env` settings when the Reflex backend starts, without overriding variables explicitly set in the process environment.
- Include safe status and endpoint context in diagnostics, with URL sanitization that excludes user information, query strings, and fragments.
- Explicitly document and support `XANO_SERVICES_URL` as the base URL for the Xano service group, while retaining the current `XANO_API_URL` fallback when the service URL is unset.
- Redact message text and log only safe failure metadata for service-message operations and their exception handlers.
- Add focused tests for diagnostic classification, configuration precedence/fallback, safe endpoint formatting, and private-data redaction.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `authentication/driver-login`: Distinguish configuration, transport, HTTP, and malformed-response failures with safe actionable context, preserving existing successful login behavior and credential rejection feedback.
- `service-request-messages`: Document the service-group base URL and fallback contract and prevent conversation text or raw exception details from appearing in logs.

## Impact

- **Within MVP:** Yes. This improves the reliability and privacy of existing authentication and service-request communication flows.
- **Likely code/documentation areas:** Existing Xano URL helpers and login handler in `sosdrive.py`, service-message request/error logging, README environment configuration, `.env.example`, and focused Python tests.
- **Domain model:** No changes to Motorista, Prestador, Tipo de Socorro, Chamado, Avaliação, or Localização. Message content remains part of the existing conversation behavior and is not persisted or displayed differently.
- **Reuse:** Reuse the existing server-side Reflex login flow, Xano HTTP helpers, service URL selector, and service-message UI; do not create parallel clients or screens.
- **Xano/API:** No Xano endpoint, schema, or authorization change. The tagged endpoint already exists and must remain untouched.
- **Compatibility:** Continue using `XANO_API_URL` as the fallback when `XANO_SERVICES_URL` is unset, and preserve successful requests for valid existing setups.
- **Rollback:** No data migration is required. Rollback may revert the client diagnostics, environment documentation, and log redaction without changing Xano resources or authorization.
