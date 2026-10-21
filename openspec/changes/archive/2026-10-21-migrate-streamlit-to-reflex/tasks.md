## 1. Specification and dependency migration

- [x] 1.1 Validate proposal, specs, design, and tasks with `openspec validate migrate-streamlit-to-reflex --type change --strict` (verification)
- [x] 1.2 Use a pinned Reflex dependency and retain required HTTP dependencies (new runtime)
- [x] 1.3 Update setup and project configuration to install and start Reflex (tooling)

## 2. Reflex application

- [x] 2.1 Create the Reflex app entrypoint and root route (new frontend runtime)
- [x] 2.2 Convert the landing hero, sections, CTA, responsive styling, local assets, and reduced-motion behavior to Reflex components (new frontend implementation)
- [x] 2.3 Convert the login and authenticated states to Reflex `rx.State` events while preserving Xano authorization boundaries (backend integration boundary)
- [x] 2.4 Remove legacy imports, session state, rerun/stop calls, and framework-only rendering APIs (breaking migration cleanup)

## 3. Documentation and project context

- [x] 3.1 Update README and setup instructions to Reflex (documentation)
- [x] 3.2 Update AGENTS, project overview, OpenSpec context, and relevant change documentation to identify Reflex as the frontend framework (documentation)
- [x] 3.3 Update style module naming/docstrings and any framework-specific references (cleanup)

## 4. Verification

- [x] 4.1 Install the declared dependencies and run Python compilation checks (verification)
- [x] 4.2 Run the Reflex production build and verify the landing page compiles (verification)
- [x] 4.3 Run mocked login checks for success, invalid credentials, missing configuration, and connection errors (verification)
- [x] 4.4 Search active project files for legacy framework references and confirm the runtime migration is complete (verification)
- [x] 4.5 Re-run strict OpenSpec validation (verification)
