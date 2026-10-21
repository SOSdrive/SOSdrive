## Purpose

Permitir que novos usuários iniciem o cadastro escolhendo claramente entre cliente/motorista e prestador, sem persistir dados até que a integração com o backend seja implementada.

## ADDED Requirements

### Requirement: The primary CTA opens account creation
The public presentation MUST open the account creation screen when the visitor activates `Conhecer a SOS Drive`.

#### Scenario: Open signup from the landing page
- **GIVEN** the visitor is on the public presentation
- **WHEN** the visitor activates `Conhecer a SOS Drive`
- **THEN** the application shows the account creation screen
- **AND** the application does not call Xano or any database

### Requirement: The visitor selects an account role
The account creation screen MUST offer exactly two visible role choices: `Cliente / Motorista` and `Prestador de serviço`.

#### Scenario: Select client role
- **GIVEN** the account creation screen is visible
- **WHEN** the visitor selects `Cliente / Motorista`
- **THEN** the selected role is visibly highlighted
- **AND** the form identifies the account as a client/motorist account

#### Scenario: Select provider role
- **GIVEN** the account creation screen is visible
- **WHEN** the visitor selects `Prestador de serviço`
- **THEN** the selected role is visibly highlighted
- **AND** the form identifies the account as a service-provider account

### Requirement: The signup form validates locally without persistence
The account creation screen MUST collect name, email, and password and MUST validate required values locally without sending them to a backend or database.

#### Scenario: Submit a complete local form
- **GIVEN** a role, name, email, and password have been provided
- **WHEN** the visitor submits the form
- **THEN** the application shows a local confirmation that the registration is prepared
- **AND** no network or database request is made
- **AND** the password is cleared from the client state after submission

#### Scenario: Submit incomplete form
- **GIVEN** one or more required values are missing
- **WHEN** the visitor submits the form
- **THEN** the application shows a validation message
- **AND** it does not show a success confirmation
- **AND** no network or database request is made

### Requirement: Existing users can choose login
The signup screen MUST provide a `Já tenho uma conta` action that opens the existing login screen without making a backend request.

#### Scenario: Switch from signup to login
- **GIVEN** the signup screen is visible
- **WHEN** the visitor activates `Já tenho uma conta`
- **THEN** the existing login screen is shown
- **AND** no network or database request is made
