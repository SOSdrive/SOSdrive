## MODIFIED Requirements

### Requirement: Service requests use the configured service-group URL
The system MUST use `XANO_SERVICES_URL` as the base URL for service-request and service-message operations when it is configured. If `XANO_SERVICES_URL` is unset or blank, the system MUST preserve the backward-compatible fallback to `XANO_API_URL`. Project setup documentation MUST identify `XANO_SERVICES_URL` as the base URL for the separate Xano service group when one is used.

#### Scenario: Service-group URL is configured
- **GIVEN** `XANO_SERVICES_URL` contains the configured service-group base URL
- **WHEN** the client sends a service-request or service-message call
- **THEN** it builds the request endpoint from `XANO_SERVICES_URL`
- **AND** it does not silently substitute `XANO_API_URL`

#### Scenario: Service-group URL is unset
- **GIVEN** `XANO_SERVICES_URL` is unset or blank and `XANO_API_URL` is configured
- **WHEN** the client sends a service-request or service-message call
- **THEN** it builds the request endpoint from `XANO_API_URL`
- **AND** existing valid setups continue to work without requiring a new environment variable

#### Scenario: Service-group URL is documented
- **GIVEN** an operator configures SOS Drive for a separate Xano service group
- **WHEN** the operator follows the project setup documentation
- **THEN** the documentation identifies `XANO_SERVICES_URL` as that group's base URL
- **AND** explains the `XANO_API_URL` fallback when the service URL is unset

### Requirement: Service-message diagnostics do not disclose conversation content
The system MUST NOT log complete service-message text, authentication credentials, full response bodies, or raw exception details for service-message operations. Service-message diagnostics MAY include safe operation metadata, exception category, HTTP status, and sanitized endpoint context.

#### Scenario: Message is sent
- **GIVEN** an authenticated user submits a service message
- **WHEN** the client sends the message to Xano
- **THEN** logs do not contain the message text or authentication token
- **AND** any diagnostic metadata is limited to safe operation and endpoint context

#### Scenario: Message request fails
- **GIVEN** a service-message request fails with an HTTP, network, or response-parsing error
- **WHEN** the failure is logged or reported to the user
- **THEN** logs do not contain the message text, raw exception text, token, or full response body
- **AND** safe failure metadata such as operation, exception category, status, or sanitized endpoint context may be recorded
- **AND** the user receives a safe, non-sensitive error message
