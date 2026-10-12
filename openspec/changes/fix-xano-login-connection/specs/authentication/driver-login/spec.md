## MODIFIED Requirements

### Requirement: The login screen authenticates through Xano
The system MUST submit the current email and password values to the configured Xano `POST auth/login` endpoint as JSON with `Content-Type: application/json`. The login action MUST provide visible loading feedback and MUST prevent duplicate submissions while a request is in progress.

#### Scenario: Submit login credentials
- **GIVEN** a configured Xano API base URL and populated login fields
- **WHEN** the user submits the login form
- **THEN** the application sends a JSON request containing the current `email` and `password` to `<XANO_API_URL>/auth/login`
- **AND** the login action displays a loading state and is disabled until the request completes
- **AND** the password is not persisted after the request

#### Scenario: Successful authentication for a client
- **GIVEN** Xano accepts the credentials and the authenticated account role is `cliente`
- **WHEN** the login request succeeds
- **THEN** the application stores the returned authentication token and user identity in current server-side Reflex state
- **AND** the application redirects to `/perfil-cliente`

#### Scenario: Successful authentication for a provider
- **GIVEN** Xano accepts the credentials and the authenticated account role is `prestador`
- **WHEN** the login request succeeds
- **THEN** the application stores the returned authentication token and user identity in current server-side Reflex state
- **AND** the application redirects to `/perfil-prestador`

#### Scenario: Invalid credentials
- **GIVEN** Xano responds with HTTP 400 or 401 for the submitted credentials
- **WHEN** the login request completes
- **THEN** the application remains on the login screen
- **AND** it displays the safe message supplied by Xano or `E-mail ou senha incorretos.`
- **AND** the password is not displayed or persisted

#### Scenario: Xano connection fails
- **GIVEN** the Xano server cannot be reached or the request fails because of a network or endpoint configuration problem
- **WHEN** the user submits the login form
- **THEN** the application remains on the login screen
- **AND** it displays `Erro ao conectar com o servidor Xano. Verifique a URL do endpoint ou sua conexão com a internet.`
- **AND** it does not expose raw exception details, passwords, or tokens

#### Scenario: Account role is not supported
- **GIVEN** Xano accepts the credentials but the authenticated account has no supported role
- **WHEN** the login flow resolves the account identity
- **THEN** the application does not redirect to either profile route
- **AND** it displays a safe message that the account type is invalid

### Requirement: Login configuration is explicit and safe
The system MUST read the Xano API base URL from `XANO_API_URL`, MUST NOT send credentials when the setting is missing or invalid, and MUST NOT persist the submitted password or expose the authentication token to browser local storage.

#### Scenario: Missing or invalid API configuration
- **GIVEN** `XANO_API_URL` is missing or is not a valid HTTP(S) base URL
- **WHEN** the user submits the login form
- **THEN** the application displays the Xano connection error
- **AND** it does not send the credentials to any endpoint

#### Scenario: Authentication token remains server-side
- **GIVEN** Xano returns an authentication token
- **WHEN** the application establishes the authenticated session
- **THEN** the token remains in server-side Reflex state
- **AND** it is not written to browser local storage or exposed in user-facing messages
