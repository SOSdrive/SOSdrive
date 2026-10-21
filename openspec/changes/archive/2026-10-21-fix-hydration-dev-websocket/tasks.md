## 1. Valid document structure and client initialization

- [x] 1.1 Replace the existing raw HTML head fragments with semantic Reflex stylesheet and script resources; compile the app and verify the generated `<head>` contains no Reflex HTML wrapper `<div>`.
- [x] 1.2 Initialize existing Leaflet map helpers only after Leaflet is available and after client mounting; verify map routes still initialize while browser hydration completes without mismatch warnings.

## 2. Development WebSocket and service readiness

- [x] 2.1 Align Reflex frontend HMR and backend WebSocket targets with the active configured host and ports without hardcoded stale URLs; run on non-default ports and verify both browser WebSocket connections succeed.
- [x] 2.2 Verify the frontend and backend listeners before browser testing and document the safe local startup/readiness check; confirm unavailable ports and port conflicts are reported without terminating unrelated processes.

## 3. Integration verification

- [x] 3.1 Run the Reflex compile and focused existing tests, then open the login and map routes in a browser; confirm no hydration mismatch, stale-port WebSocket error, or regression in map functionality.
- [x] 3.2 Validate the change with `openspec validate fix-hydration-dev-websocket --type change --strict`.
