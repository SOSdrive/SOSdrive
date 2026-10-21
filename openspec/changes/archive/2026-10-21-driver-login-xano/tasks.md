## 1. OpenSpec and configuration

- [x] 1.1 Validate the proposal, capability spec, design, and task list with `openspec validate driver-login-xano --type change --strict` (verification)
- [x] 1.2 Document the Xano base URL configuration without committing secrets (reuse existing project configuration patterns)

## 2. Login integration

- [x] 2.1 Add a small Xano login client using the existing Python HTTP dependency and the `POST auth/login` contract (new integration; backend authorization remains in Xano)
- [x] 2.2 Handle missing configuration, invalid credentials, connection failures, and malformed successful responses without exposing passwords or tokens (backend response boundary)

## 3. Reflex flow

- [x] 3.1 Make `Conhecer a SOS Drive` navigate to the login screen while preserving the public presentation as the return path (reuse existing landing state)
- [x] 3.2 Add email/password form, submit action, accessible feedback, and authenticated Reflex state without persisting the password (new screen behavior)
- [x] 3.3 Add a logout/return-safe state transition for the current session (new session behavior)

## 4. Verification

- [x] 4.1 Run `python -m py_compile presentation_screen.py styles.py` (verification)
- [x] 4.2 Run focused tests or a mocked request check for the successful Xano contract (verification)
- [x] 4.3 Validate the change with `openspec validate driver-login-xano --type change --strict` (verification)
