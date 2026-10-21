## Context

The current application is a single legacy script with a shared CSS injector. It contains a public landing page, a login route controlled by framework state, and a requests-based Xano client. Reflex uses declarative components and server-side `rx.State`, so the UI and event flow must be converted rather than mechanically renamed.

## Decisions

### Application structure

Use a standard Reflex project entrypoint, `sosdrive.py`, with an `rx.App` and route components. Keep `presentation_screen.py` as a compatibility-free implementation surface only if needed during the migration; the documented runtime entrypoint will be the Reflex app.

### State and events

Create a Reflex state class with:

- `screen`: `presentation`, `login`, or `authenticated`;
- `email` and `password` as transient form values, clearing password after submit;
- `auth_token` and `user_id` only after successful Xano authentication;
- `error_message` and loading state for feedback.

Use event handlers for navigation, form field updates, login, and logout. Do not use legacy session state or rerun/stop primitives.

### Xano integration

Reuse the existing endpoint contract and `requests` client. Read `XANO_API_URL` from the process environment, normalize the base URL, call `/auth/login`, and translate failures into safe user-facing state. The endpoint remains responsible for password validation and authorization.

### Styling and assets

Move CSS into Reflex global styles or a static CSS file and preserve the existing visual tokens, responsive rules, reduced-motion behavior, and local image fallback. Use Reflex components for semantic structure instead of framework-specific HTML injection.

### Documentation and setup

Update `requirements.txt`, `setup.ps1`, `README.md`, `AGENTS.md`, `docs/project-overview.md`, and `openspec/config.yaml`. The documented command becomes `reflex run`, normally serving the Reflex app on port 3000.

## Compatibility and rollback

This is a breaking frontend runtime migration. Rollback is the previous commit/change state, where the previous framework remains the runtime. Xano endpoints and domain data are unchanged, so no data rollback is required.

## Verification

- Validate the change with `openspec validate migrate-streamlit-to-reflex --type change --strict`.
- Install Reflex in the project environment.
- Run `python -m py_compile` on all Python modules.
- Run `reflex run` and verify the landing page at the documented local URL.
- Test CTA navigation, successful login, invalid credentials, missing Xano configuration, and logout with mocked HTTP responses.
- Search active project files to confirm no legacy imports, commands, dependency declarations, or architecture instructions remain.
