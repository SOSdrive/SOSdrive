# Reflex Application

## ADDED Requirements

### Requirement: The SOS Drive web app runs with Reflex
The project MUST provide a Reflex application entrypoint and MUST NOT require the previous framework to start the public web experience.

#### Scenario: Start the application locally
- **GIVEN** the project dependencies are installed
- **WHEN** the developer runs the documented Reflex start command
- **THEN** the application starts the public SOS Drive landing page
- **AND** no previous-framework executable or import is required

#### Scenario: Render the public presentation
- **GIVEN** the application is running
- **WHEN** a visitor opens the root route
- **THEN** the landing page renders the existing SOS Drive presentation content
- **AND** the page remains responsive on desktop and mobile viewports

### Requirement: The Reflex UI preserves the login navigation flow
The application MUST preserve the public-to-login navigation and authenticated state using Reflex state.

#### Scenario: Open login from the primary CTA
- **GIVEN** the visitor is on the public presentation
- **WHEN** the visitor activates `Conhecer a SOS Drive`
- **THEN** the application renders the email and password login form
- **AND** no authenticated request is made until the form is submitted

#### Scenario: Authenticate through Xano
- **GIVEN** `XANO_API_URL` is configured and the visitor submits valid credentials
- **WHEN** the Reflex event handler calls Xano `POST /auth/login`
- **THEN** the application stores the returned token and user id in server-side Reflex state
- **AND** the password is not persisted in state or displayed in the UI

#### Scenario: Handle login failures
- **GIVEN** Xano rejects the credentials, is unavailable, or is not configured
- **WHEN** the visitor submits the login form
- **THEN** the application remains on the login flow
- **AND** it shows a generic actionable error without exposing tokens, passwords, or raw exception details

### Requirement: Framework references are consistent
Project runtime documentation, setup instructions, dependency declarations, and architecture context MUST identify Reflex as the frontend framework and MUST contain no active legacy implementation references.

#### Scenario: Inspect the project setup
- **GIVEN** a developer reads the README, setup script, requirements, agent rules, or architecture context
- **WHEN** they follow the documented installation and run instructions
- **THEN** those instructions install and start Reflex
- **AND** they do not instruct the developer to install or run the previous framework
