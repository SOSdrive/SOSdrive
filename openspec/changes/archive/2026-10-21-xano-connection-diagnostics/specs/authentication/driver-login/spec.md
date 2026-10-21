## MODIFIED Requirements

### Requirement: Login reports actionable and safe Xano failures
The system MUST distinguish missing or invalid `XANO_API_URL`, network
failures, non-credential HTTP failures, and malformed successful responses.
Diagnostics MUST identify the failed endpoint and HTTP status when available,
without exposing URL credentials, query strings, fragments, passwords, tokens,
full response bodies, or raw exception text.
The backend MUST load project-local `.env` settings at startup without
overriding values explicitly provided by the process environment.

#### Scenario: Xano configuration is provided in the project environment file
- **GIVEN** a valid `XANO_API_URL` is set in the project-root `.env` file
- **AND** the backend process does not already define `XANO_API_URL`
- **WHEN** the Reflex backend starts and the user submits login
- **THEN** the backend uses the `.env` value to call `/auth/login`
- **AND** it does not report that `XANO_API_URL` is missing

#### Scenario: Process configuration takes precedence over the environment file
- **GIVEN** `XANO_API_URL` is set both in the process environment and project
  `.env`
- **WHEN** the backend starts
- **THEN** the backend uses the process environment value

#### Scenario: Xano API URL is missing or invalid
- **GIVEN** `XANO_API_URL` is missing or is not a valid HTTP(S) base URL
- **WHEN** the user submits the login form
- **THEN** the system does not send credentials to Xano
- **AND** it reports whether the variable is missing or invalid and explains how
  to configure the base URL
- **AND** the backend log identifies the configuration failure without logging
  credentials or submitted form data

#### Scenario: Login request fails before an HTTP response
- **GIVEN** the configured Xano endpoint cannot be reached or times out
- **WHEN** the login request is made
- **THEN** the user receives safe network troubleshooting guidance
- **AND** the backend logs the sanitized endpoint and exception category, but
  not the raw exception text

#### Scenario: Xano returns an HTTP failure
- **GIVEN** a configured login or authenticated-user endpoint returns a
  non-success HTTP status
- **WHEN** the login flow handles the response
- **THEN** credential-rejection statuses preserve the existing safe
  invalid-credentials feedback
- **AND** other statuses are reported with the status code and endpoint path
- **AND** response bodies and URL credentials, query strings, and fragments are
  not included in diagnostics

#### Scenario: Xano returns a malformed successful response
- **GIVEN** an authentication endpoint returns invalid JSON or a response that
  lacks required authentication or identity fields
- **WHEN** the login flow processes the response
- **THEN** the user receives safe guidance to check the Xano endpoint contract
- **AND** diagnostics identify the sanitized endpoint and HTTP status without
  logging response content or authentication data
