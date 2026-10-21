## 1. Form submission and loading

- [x] 1.1 Reuse the existing Reflex login form and ensure its submit action invokes the async authentication event exactly once; verify clicking `Entrar` and pressing Enter both start the event.
- [x] 1.2 Disable the submit button while authentication is pending and show `Entrando...` or an equivalent spinner; verify duplicate submissions are prevented and the button is restored after success and failure.

## 2. Xano request configuration and error handling

- [x] 2.1 (backend) Validate and normalize `XANO_API_URL` before sending credentials, then submit current email/password as JSON to `POST /auth/login`; verify mocked requests assert URL, method, JSON payload, content type, and timeout.
- [x] 2.2 (backend) Map HTTP 400/401 to a safe Xano message or `E-mail ou senha incorretos.`, and map missing/invalid configuration and network failures to the exact connection message; verify mocks for each branch and confirm no raw exception or secret is exposed.
- [x] 2.3 (backend) Clear the password and loading state on every completion path; verify both values are cleared/reset after mocked success, invalid credentials, and connection failure.

## 3. Successful session and role routing

- [x] 3.1 (backend) Preserve the authentication token and identity only in server-side Reflex state, resolve the normalized account role, and redirect clients/providers to their profile routes; verify each role routes correctly and unsupported roles do not redirect.
- [x] 3.2 (backend) Support the documented Xano token field variants while validating the successful response contract; verify malformed responses are handled safely and the token is absent from browser localStorage.

## 4. End-to-end verification

- [x] 4.1 Run focused login tests and exercise the rendered login form with mocked Xano success, HTTP 400/401, and network failure; verify feedback, loading behavior, profile routing, and that no browser-to-Xano CORS dependency was introduced.
- [x] 4.2 Validate the change with `openspec validate fix-xano-login-connection --type change --strict` and confirm existing login/navigation tests still pass.
