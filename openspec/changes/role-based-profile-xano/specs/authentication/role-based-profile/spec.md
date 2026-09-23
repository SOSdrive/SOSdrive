## Purpose

Esta capacidade direciona cada conta autenticada para sua jornada de cliente ou prestador e fornece um perfil cadastral persistido no Xano, sempre limitado ao usuário do token atual.

## ADDED Requirements

### Requirement: The authenticated role selects the user profile route
The system MUST accept only the roles `cliente` and `prestador` for this flow, expose the role in the authenticated user payload, and route the user to the matching profile route after a successful login.

#### Scenario: Client login is redirected to the client profile
- **GIVEN** Xano authenticates a user whose role is `cliente`
- **WHEN** the login completes successfully
- **THEN** the application stores the authenticated session and navigates to `/perfil-cliente`

#### Scenario: Provider login is redirected to the provider profile
- **GIVEN** Xano authenticates a user whose role is `prestador`
- **WHEN** the login completes successfully
- **THEN** the application stores the authenticated session and navigates to `/perfil-prestador`

#### Scenario: Unsupported role is rejected
- **GIVEN** the authenticated user has a role other than `cliente` or `prestador`
- **WHEN** the application receives the authenticated user payload
- **THEN** the session is not granted access to a profile route
- **AND** the user receives a recoverable configuration or authorization error

### Requirement: The profile page displays and edits the authenticated user's profile
The system MUST provide both role-specific profile routes with fields for profile photo, full name, CPF, and phone number, plus an action to save or update the data.

#### Scenario: Existing profile is loaded
- **GIVEN** an authenticated user opens the profile route matching their role
- **WHEN** the profile page loads
- **THEN** the application requests the profile for the current authenticated user
- **AND** it displays the returned photo, full name, CPF, and phone when present

#### Scenario: Profile fields are saved
- **GIVEN** an authenticated user enters valid profile data
- **WHEN** the user activates `Salvar/Atualizar Dados`
- **THEN** the application sends the profile data to the authenticated profile endpoint
- **AND** it shows a success state without exposing the authentication token

#### Scenario: Invalid profile data is rejected
- **GIVEN** a profile field fails the applicable validation or mask rule
- **WHEN** the user tries to save
- **THEN** the application does not submit the invalid payload
- **AND** it shows an error state in red near the form

### Requirement: Profile access is authorized by the backend
The profile API MUST derive the target `user_id` from the authentication token and MUST prevent a user from reading or changing another user's profile.

#### Scenario: Authenticated user reads own profile
- **GIVEN** a valid authentication token
- **WHEN** the user calls `GET /user_profile`
- **THEN** the API returns only the profile linked to the token subject

#### Scenario: Authenticated user creates or updates own profile
- **GIVEN** a valid authentication token and a profile payload
- **WHEN** the user calls `POST /user_profile` or `PUT /user_profile`
- **THEN** the API creates or updates the single profile linked to the token subject
- **AND** it does not accept a client-supplied `user_id` as an authorization override

#### Scenario: Unauthenticated profile access is denied
- **GIVEN** a missing, invalid, or expired authentication token
- **WHEN** the user calls a profile endpoint
- **THEN** the API rejects the request with an authorization error

### Requirement: Profile presentation follows the existing visual system
The profile routes MUST use the established SOS Drive visual language: off-white background, dark navy headings and links, vivid orange primary actions, gray filled inputs without a default border, navy focus borders, clean sans-serif typography, and red error text.

#### Scenario: Profile form is rendered consistently
- **GIVEN** the profile route is visible on desktop or mobile
- **WHEN** the user inspects the form
- **THEN** inputs, save action, focus state, typography, spacing, and error state follow the same design tokens as the login flow
