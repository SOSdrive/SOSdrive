## Purpose

Define how a selected profile photo is previewed in the avatar before it is saved, while preserving the existing profile photo and initials fallback.

## ADDED Requirements

### Requirement: Profile photo selection previews before save
The profile editor MUST accept a valid image selection and show that image in the avatar before any profile save request is sent.

#### Scenario: Select a valid image
- **GIVEN** the user is editing their profile
- **WHEN** they select a valid image file
- **THEN** the avatar displays the selected image immediately
- **AND** the selected image remains staged for the existing save action
- **AND** no profile persistence request is sent until the user saves

#### Scenario: Select an unsupported or unreadable file
- **GIVEN** the user is editing their profile
- **WHEN** they select a file that is not a readable image
- **THEN** the application displays a safe validation error
- **AND** the invalid file does not replace the current avatar or staged image

### Requirement: Avatar uses the most relevant available image
The profile avatar MUST prefer the staged image, then the persisted profile photo, and show the user's initials only when neither image is available.

#### Scenario: A staged image is available
- **GIVEN** a staged image and a persisted profile photo are both available
- **WHEN** the profile avatar is rendered
- **THEN** the staged image is displayed

#### Scenario: Only a persisted image is available
- **GIVEN** there is no staged image and a persisted profile photo is available
- **WHEN** the profile avatar is rendered
- **THEN** the persisted profile photo is displayed

#### Scenario: No profile image is available
- **GIVEN** there is no staged image or persisted profile photo
- **WHEN** the profile avatar is rendered
- **THEN** the avatar displays the user's initials

### Requirement: Profile photo preview matches the circular avatar
The selected and persisted profile images MUST fill the circular avatar without distorting their aspect ratio.

#### Scenario: Render an image in the avatar
- **GIVEN** the avatar displays a staged or persisted image
- **WHEN** the image is rendered
- **THEN** it fills the avatar bounds with cover cropping
- **AND** its visible shape remains circular

### Requirement: Staged profile photo survives save errors
The application MUST retain the staged image for retry when saving the profile fails, and MUST use the saved profile photo after a successful save.

#### Scenario: Save fails
- **GIVEN** a valid image is staged
- **WHEN** the profile save request fails
- **THEN** the staged image remains visible in the avatar
- **AND** the user can retry saving without selecting the image again

#### Scenario: Save succeeds
- **GIVEN** a valid image is staged
- **WHEN** the profile save request succeeds
- **THEN** the saved profile photo becomes the avatar image
- **AND** the staged image state is cleared or synchronized with the saved photo
