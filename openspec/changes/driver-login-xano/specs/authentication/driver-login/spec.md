# Driver Login

## ADDED Requirements

### Requirement: The presentation CTA opens the driver login screen
The system MUST show the driver login screen when the user activates the primary `Conhecer a SOS Drive` action.

#### Scenario: Open login from the landing page
- **GIVEN** the public presentation is visible and the user is not authenticated
- **WHEN** the user activates `Conhecer a SOS Drive`
- **THEN** the application shows email and password fields and a login action
- **AND** the landing content is not submitted as an authenticated request

#### Scenario: Return to the landing page
- **GIVEN** the login screen is visible
- **WHEN** the user activates the return action
- **THEN** the application shows the public presentation again
- **AND** no authentication request is sent

### Requirement: The login screen authenticates through Xano
The system MUST send the submitted email and password to the configured Xano `POST auth/login` endpoint.

#### Scenario: Successful authentication
- **GIVEN** a configured Xano API base URL and valid credentials
- **WHEN** the user submits the login form
- **THEN** the application sends a JSON request containing `email` and `password` to `<XANO_API_URL>/auth/login`
- **AND** the application stores the returned `authToken` and `user_id` in current server-side Reflex state
- **AND** the application shows an authenticated success state

#### Scenario: Invalid credentials
- **GIVEN** the Xano endpoint rejects the credentials with an authorization error
- **WHEN** the user submits the login form
- **THEN** the application remains on the login screen
- **AND** the application shows a generic invalid-credentials message
- **AND** the password is not displayed back to the user

#### Scenario: Xano is unavailable
- **GIVEN** the Xano endpoint cannot be reached or returns an unexpected server failure
- **WHEN** the user submits the login form
- **THEN** the application remains on the login screen
- **AND** the application shows a recoverable connection error
- **AND** the exception details are not exposed as user-facing credentials or tokens

### Requirement: Login configuration is explicit and safe
The system MUST read the API base URL from `XANO_API_URL` and MUST NOT hard-code credentials or persist the submitted password.

#### Scenario: Missing API configuration
- **GIVEN** no Xano API base URL is configured
- **WHEN** the user submits the login form
- **THEN** the application shows a configuration error
- **AND** it does not send the credentials to any endpoint
