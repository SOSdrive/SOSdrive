## Purpose

Define reliable profile saving by ensuring the Xano request contains only values supported by the profile endpoint and preserves the current photo unless the user selects a replacement.

## ADDED Requirements

### Requirement: Profile text fields use primitive strings
The profile save request MUST send the established profile fields `nome_completo`, `cpf`, and `telefone` as strings. Missing values MUST be represented as empty strings, and CPF and telephone values MUST contain digits only.

#### Scenario: Save formatted profile details
- **WHEN** the user saves a profile with a formatted CPF or telephone number
- **THEN** the request sends `nome_completo`, `cpf`, and `telefone` as strings
- **AND** the CPF and telephone contain only digits

#### Scenario: Save empty optional fields
- **WHEN** the user saves with an empty CPF or telephone
- **THEN** the request sends an empty string for each empty field
- **AND** the request does not send `null`, `undefined`, or a non-primitive value for those fields

### Requirement: Profile photo upload returns a stable public URL
The profile editor MUST upload a newly selected image through an authenticated file-upload endpoint that returns a stable public URL. The profile save request MUST send `foto_perfil` as a string containing that URL and MUST NOT send a raw file or file object to the profile endpoint.

#### Scenario: Save a newly selected photo
- **WHEN** the user saves a profile with a newly selected photo
- **THEN** the image is uploaded to the authenticated upload endpoint
- **AND** the profile JSON sends the returned public URL as the `foto_perfil` string
- **AND** all profile fields in the JSON are primitive strings

#### Scenario: Photo upload fails
- **WHEN** the image upload fails
- **THEN** the profile save request is not sent
- **AND** the selected image remains staged for retry
- **AND** the editor displays an error rather than a success message

#### Scenario: Save without changing the photo
- **WHEN** the user saves a profile without selecting a new photo
- **THEN** the request sends the existing `foto_perfil` URL as a string, or an empty string when no photo exists
- **AND** the profile endpoint does not receive a `null` or file object for the photo
- **AND** the existing photo remains unchanged when one exists

### Requirement: Profile save feedback reflects request status
The profile editor MUST indicate that saving is in progress and MUST report success only after the profile save request succeeds.

#### Scenario: Save is in progress
- **WHEN** the profile save request is pending
- **THEN** the save action displays a loading state and prevents duplicate submissions

#### Scenario: Save succeeds
- **WHEN** the profile save request succeeds
- **THEN** the editor displays a success message

#### Scenario: Save fails
- **WHEN** the profile save request fails
- **THEN** the editor displays an error
- **AND** it does not display a success message
