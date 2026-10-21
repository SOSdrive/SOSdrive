## ADDED Requirements

### Requirement: Restore completed archived changes to the changes directory
All completed OpenSpec change packages found under `openspec/archive/` MUST be
restored under `openspec/changes/` with their names, artifacts, and contents
preserved.

#### Scenario: Completed archived changes exist
- **GIVEN** one or more completed change packages exist under
  `openspec/archive/`
- **WHEN** the restoration is performed
- **THEN** every eligible package is present under `openspec/changes/`
- **AND** its files and contents are preserved
- **AND** no package is silently discarded or overwritten

#### Scenario: No archive directory or no eligible packages exist
- **GIVEN** `openspec/archive/` does not exist or contains no completed change
  packages
- **WHEN** the restoration is checked
- **THEN** no package is moved
- **AND** the result is reported as requiring no migration

### Requirement: Preserve incomplete and conflicting change packages
The restoration MUST NOT move incomplete packages or overwrite an existing
change package with the same name. Any incomplete or conflicting package MUST
remain intact and be reported for explicit resolution.

#### Scenario: Incomplete package is found
- **GIVEN** an archived package has unfinished tasks or cannot be confirmed as
  completed
- **WHEN** the restoration is performed
- **THEN** the package remains in `openspec/archive/`
- **AND** its path and reason are reported

#### Scenario: Destination name already exists
- **GIVEN** a package with the same name already exists in `openspec/changes/`
- **WHEN** the restoration encounters that package
- **THEN** neither package is overwritten or discarded
- **AND** the conflict is reported for manual resolution

### Requirement: Remove an empty archive directory after restoration
The system MUST remove `openspec/archive/` only when it is empty after all
eligible packages are restored.

#### Scenario: All archived packages are restored
- **GIVEN** every eligible package has been moved and no packages remain in the
  archive directory
- **WHEN** the restoration completes
- **THEN** the empty `openspec/archive/` directory is removed

#### Scenario: Packages remain in the archive directory
- **GIVEN** incomplete or conflicting packages remain
- **WHEN** the restoration completes
- **THEN** `openspec/archive/` remains intact

### Requirement: Keep completed changes in the active changes directory
The project workflow MUST keep completed OpenSpec change packages under
`openspec/changes/` and MUST NOT archive them as part of completing a change.

#### Scenario: A change is completed
- **GIVEN** all implementation and verification tasks for a change are
  completed
- **WHEN** the project records the change as complete
- **THEN** its package remains under `openspec/changes/`
- **AND** the project workflow documentation instructs contributors not to
  move it to `openspec/archive/`
