## ADDED Requirements

### Requirement: Only completed changes are eligible for archival
The project MUST archive an OpenSpec change only when every applicable task is complete. For a change without `tasks.md`, explicit completion evidence in its other artifacts MUST be verified; absence of a task list alone is not evidence. When the CLI is available, OpenSpec validation MUST succeed. If completion cannot be confirmed or validation fails, the change MUST remain active.

#### Scenario: Archive a completed change
- **GIVEN** an active OpenSpec change whose applicable tasks are all marked complete
- **AND** OpenSpec validation for that change succeeds when the CLI is available
- **WHEN** the project archives the change
- **THEN** the change is eligible for the native workflow or authorized fallback

#### Scenario: Do not archive an incomplete change
- **GIVEN** an active OpenSpec change with one or more incomplete tasks or uncertain completion status
- **WHEN** archival is requested
- **THEN** the change remains in the active changes area
- **AND** the incomplete or uncertain status is reported

#### Scenario: Do not archive a change that fails validation
- **GIVEN** an active OpenSpec change whose validation reports an error
- **WHEN** archival is requested
- **THEN** the change remains in the active changes area
- **AND** the validation failure is reported

### Requirement: Completed changes use native archival when available
The project SHOULD use the archive command and destination conventions provided by the installed OpenSpec CLI. If the CLI is unavailable, an explicitly authorized fallback MAY move an eligible package intact to `openspec/changes/archive/YYYY-MM-DD-<change>`. The fallback MUST NOT edit, omit, or merge package contents. An archived change MUST no longer be active and its artifacts MUST remain available.

#### Scenario: Archive through the native CLI
- **GIVEN** a change passed the completion and validation preconditions
- **WHEN** an authorized operator confirms the native OpenSpec archive operation
- **THEN** the CLI archives the change according to its native archive conventions
- **AND** the change is no longer listed as active
- **AND** its archived artifacts remain accessible

#### Scenario: Native CLI is unavailable
- **GIVEN** the OpenSpec CLI is unavailable and the package meets completion criteria
- **WHEN** an operator uses the authorized fallback
- **THEN** the complete package is moved intact to the dated OpenSpec archive location
- **AND** the unavailable CLI and skipped native validation are reported
- **AND** incomplete or uncertain packages remain active

### Requirement: Archive conflicts are handled without data loss
The project MUST NOT overwrite, merge, discard, or automatically rename an existing archive package or active change to resolve a destination conflict. On conflict or ambiguous CLI failure, the operation MUST be treated as blocked, and existing content MUST be preserved for explicit resolution.

#### Scenario: Archive destination already exists
- **GIVEN** a native archive destination conflicts with the change being archived
- **WHEN** the conflict is detected before or during the native operation
- **THEN** the operation is not forced
- **AND** neither the active change nor the existing archived content is overwritten or removed
- **AND** the conflict is reported for explicit resolution

#### Scenario: Native archive operation fails ambiguously
- **GIVEN** the CLI reports an error or its result cannot be confirmed
- **WHEN** the operator checks the active and archive locations
- **THEN** no manual compensating move or overwrite is performed
- **AND** any copies or partial state are preserved for inspection
- **AND** the archival is not reported as successful until its state is resolved and verified

### Requirement: Archival outcome is verified
After native or fallback archival, the project MUST verify that the selected change is absent from the active change area and present in the archive with its artifacts preserved. Changes not selected for archival MUST remain unchanged.

#### Scenario: Verify a successful archive
- **GIVEN** native or fallback archival has completed
- **WHEN** the operator verifies the result
- **THEN** the selected change is absent from the active changes area
- **AND** its archived artifacts are present and structurally intact in the native archive
- **AND** unselected changes remain unchanged

#### Scenario: Verification detects missing or altered artifacts
- **GIVEN** post-archive verification finds missing, altered, or unaccounted-for artifacts
- **WHEN** the result is reviewed
- **THEN** the operation is not considered successfully verified
- **AND** no conflicting content is overwritten during investigation
- **AND** the discrepancy is reported for explicit recovery without overwriting content
