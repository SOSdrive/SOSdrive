# Driver Login Migration

## MODIFIED Requirements

### Requirement: The driver login remains backed by Xano
The driver login MUST keep using the existing Xano `POST /auth/login` contract while its UI and state management use Reflex.

#### Scenario: Successful login after migration
- **GIVEN** a configured Xano base URL and valid driver credentials
- **WHEN** the driver submits the Reflex login form
- **THEN** the application sends `email` and `password` as JSON to `<XANO_API_URL>/auth/login`
- **AND** stores only the returned `authToken` and `user_id` in authenticated server-side state

#### Scenario: Invalid credentials after migration
- **GIVEN** Xano returns an authorization failure
- **WHEN** the driver submits the login form
- **THEN** the application shows a generic invalid-credentials message
- **AND** remains unauthenticated
- **AND** does not expose the password or token
