## MODIFIED Requirements

### Requirement: The login screen authenticates through Xano and routes by role
The system MUST send the submitted email and password to the configured Xano `POST auth/login` endpoint, retain the returned authentication session, obtain the authenticated user's role, and route only supported roles to their corresponding profile route.

#### Scenario: Successful client authentication
- **GIVEN** a configured Xano API base URL and valid credentials for a user with role `cliente`
- **WHEN** the user submits the login form
- **THEN** the application sends a JSON request containing `email` and `password` to `<XANO_API_URL>/auth/login`
- **AND** it stores the returned `authToken` and user identifier in current server-side session state
- **AND** it obtains the authenticated role
- **AND** it redirects the user to `/perfil-cliente`
- **AND** it does not persist the submitted password

#### Scenario: Successful provider authentication
- **GIVEN** a configured Xano API base URL and valid credentials for a user with role `prestador`
- **WHEN** the user submits the login form
- **THEN** the application redirects the user to `/perfil-prestador`
- **AND** it does not expose the authentication token in the rendered page

#### Scenario: Unsupported authenticated role
- **GIVEN** Xano returns a role other than `cliente` or `prestador`
- **WHEN** authentication completes
- **THEN** the application does not redirect to a profile route
- **AND** it shows a recoverable authorization error

#### Scenario: Invalid credentials
- **GIVEN** the Xano endpoint rejects the credentials with an authorization error
- **WHEN** the user submits the login form
- **THEN** the application remains on the login screen
- **AND** it shows a generic invalid-credentials message
- **AND** the password is not displayed back to the user

#### Scenario: Xano is unavailable
- **GIVEN** the Xano endpoint cannot be reached or returns an unexpected server failure
- **WHEN** the user submits the login form
- **THEN** the application remains on the login screen
- **AND** the application shows a recoverable connection error
- **AND** exception details, credentials, and tokens are not exposed to the user

### Requirement: Login configuration is explicit and safe
The system MUST read the API base URL from `XANO_API_URL`, MUST NOT hard-code credentials, and MUST NOT persist the submitted password.

#### Scenario: Missing API configuration
- **GIVEN** no Xano API base URL is configured
- **WHEN** the user submits the login form
- **THEN** the application shows a configuration error
- **AND** it does not send the credentials to any endpoint
