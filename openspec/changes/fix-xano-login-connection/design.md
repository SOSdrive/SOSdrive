## Context

See `proposal.md` for motivation and `specs/authentication/driver-login/spec.md` for the updated behavior. The login form, Xano client, server-side session state, and profile routes already exist in `sosdrive.py`. A previous change defined the same `authentication/driver-login` capability, but this repository has not yet synced that capability into a canonical `openspec/specs/` file.

## Goals / Non-Goals

**Goals:**
- Ensure one submit path drives login, loading feedback, and error reset/completion.
- Make the server-side Xano request contract and its failure cases explicit and testable.
- Preserve server-side token handling and route authenticated accounts by normalized role.

**Non-Goals:**
- Add a browser-to-Xano request, CORS policy, or localStorage token persistence.
- Change Xano endpoints, user credentials, database records, or authorization rules.
- Add an unrelated login, signup, or profile experience.

## Decisions

### Keep authentication requests server-side

Use the existing Reflex event handler and Python HTTP client to call Xano. A server-to-server request is not subject to browser CORS enforcement; therefore, do not move authentication into client-side JavaScript or recommend permissive CORS as a workaround. Check the base URL, endpoint, response status, timeout, and backend connectivity instead.

### Validate and normalize the Xano base URL before sending credentials

Read `XANO_API_URL` through the existing configuration helper, require an HTTP(S) URL with a host, trim whitespace and trailing slashes, and append exactly `/auth/login`. Submit the current state values as `{"email": ..., "password": ...}` using the HTTP client's JSON request parameter, which sets the JSON content type. Keep the existing timeout and never log the password or token.

### Resolve the authenticated role before redirect

After successful authentication, retain token and identity only in server-side Reflex state and use the existing authenticated-user loading/role-normalization path. Redirect `cliente` to `/perfil-cliente` and `prestador` to `/perfil-prestador`; reject unsupported/missing roles without routing to an unrelated page. Do not put the token in LocalStorage, even though the initial request suggested it, because the requester confirmed the existing server-side session model.

### Map errors to safe user feedback

Handle Xano HTTP 400/401 as invalid credentials, preferring a safe message field returned by Xano and falling back to `E-mail ou senha incorretos.`. Map connection, timeout, invalid configuration, and unavailable-server failures to the exact requested connection message. Keep raw exception data and untrusted response bodies out of logs and user-facing messages. Clear the password and loading state in a `finally` path.

## Risks / Trade-offs

- [Xano error response schemas can vary] → Parse only known human-readable message fields and use the specified fallback when none is available.
- [The configured base URL may omit the API group or contain a trailing slash] → Validate the HTTP(S) URL and normalize it once before appending `/auth/login`.
- [CORS terminology may distract from a backend connection failure] → Keep the HTTP call server-side and report endpoint/network troubleshooting without changing browser CORS settings.
- [Role lookup may fail after credentials are accepted] → Do not redirect until the authenticated role has been resolved and validated; show a safe recoverable error.

## Migration Plan

No data or dependency migration is needed. Preserve the existing server-side session contract. If the change must be rolled back, restore the previous login handler and redirect behavior without changing Xano data or credentials.

## Verification

- Mock the HTTP client and assert method, normalized endpoint, JSON payload, JSON content type, and timeout without printing credentials.
- Cover missing/invalid `XANO_API_URL`, HTTP 400 and 401, timeouts/connection errors, malformed success responses, supported and unsupported roles.
- Verify loading/disabled behavior during submission and password clearing after completion.
- Verify the client and provider profile routes after successful login and confirm token is absent from browser LocalStorage.
- Run the existing focused Python tests and OpenSpec strict validation.
