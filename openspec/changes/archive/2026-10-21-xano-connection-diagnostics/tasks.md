## 1. Login diagnostics

- [x] 1.0 (backend; reuse Python dotenv) Load `.env` from the project root at backend startup without overriding process-provided variables; add a placeholder `.env.example` and dependency declaration.
- [x] 1.1 (backend; reuse existing login flow) Classify missing/invalid configuration, transport failures, HTTP failures, and malformed success responses separately; preserve successful login routing and server-side session behavior.
- [x] 1.2 (backend; reuse existing Xano client) Add safe diagnostic endpoint formatting and include HTTP status where available; exclude URL user information, query strings, fragments, credentials, tokens, response bodies, and raw exception text.
- [x] 1.3 (backend; reuse existing test suite) Add mocked tests for configuration failures with no request, network/timeout errors, credential-rejection statuses, other HTTP statuses, malformed JSON, and incomplete success responses. Assert actionable category/context and exact secret redaction.

## 2. Service-group configuration and message privacy

- [x] 2.1 (backend; reuse existing URL helper) Confirm `XANO_SERVICES_URL` takes precedence for service-request and service-message calls, preserving `XANO_API_URL` fallback only when the service URL is unset or blank; do not change authorization behavior.
- [x] 2.2 (documentation; update existing setup guidance) Explain how to configure `.env` and `XANO_API_URL`, that `XANO_SERVICES_URL` points to the separate Xano service group, and document the fallback to `XANO_API_URL`.
- [x] 2.3 (backend; reuse existing message handlers) Remove message bodies and raw exception details from service-message logs; retain only safe operation, status, exception category, and sanitized endpoint metadata.
- [x] 2.4 (backend; reuse existing test suite) Add tests for configured service URL precedence and unset/blank fallback, and captured-log tests proving message text, tokens, and raw exception content are not logged on success or failure.

## 3. Validation and boundaries

- [x] 3.1 Run focused Python tests for login diagnostics, service URL selection, and service-message log redaction; confirm valid existing request and login paths remain compatible.
- [x] 3.2 Check OpenSpec validation if the CLI is available; do not modify Xano endpoint files or authorization rules. The OpenSpec CLI is unavailable in this environment, so strict CLI validation could not run.
