## ADDED Requirements

### Requirement: A service request has many messages
The system MUST persist zero or more messages for each service request, and each message MUST belong to exactly one service request.

#### Scenario: Message relationship
- **GIVEN** a service request exists
- **WHEN** one or more messages are created for it
- **THEN** every message stores the request identifier in `service_request_id`
- **AND** querying by `service_request_id` returns all messages for that request

### Requirement: Authenticated users can create request messages
The system MUST expose `POST /service_requests/{id}/messages` with a `message_text` input and return the created message.

#### Scenario: Create message
- **GIVEN** a valid authenticated user and an existing service request
- **WHEN** the user submits non-empty `message_text`
- **THEN** the API creates one message with the URL request id and `$auth.id` as `sender_id`
- **AND** returns the created record

#### Scenario: Invalid request or message
- **GIVEN** a missing request or blank message text
- **WHEN** the endpoint is called
- **THEN** no message is created
- **AND** the API returns an error

### Requirement: Request status supports controlled completion
The system MUST expose `PATCH /service_requests/{id}` and allow `completed` only from `accepted` or `in_progress`.

#### Scenario: Complete accepted or in-progress request
- **GIVEN** an authenticated request with status `accepted` or `in_progress`
- **WHEN** the status is patched to `completed`
- **THEN** the request is updated and the API returns the updated record

#### Scenario: Reject invalid completion transition
- **GIVEN** a request with any other status
- **WHEN** the status is patched to `completed`
- **THEN** the request remains unchanged
- **AND** the API returns an error

### Requirement: Authenticated users can read request messages
The system MUST expose `GET /service_requests/{id}/messages` and return the messages for the requested service request in creation order.

#### Scenario: Load conversation
- **GIVEN** a valid authenticated user and an existing service request
- **WHEN** the client requests the conversation
- **THEN** the API returns the request messages ordered from oldest to newest
- **AND** the client can render the message text and sender identifier

### Requirement: The client can use the request conversation
The client application MUST show a conversation action when it has an active service request and MUST allow the authenticated client to load and send messages for that request.

#### Scenario: Client opens the conversation
- **GIVEN** the client has an active service request identifier
- **WHEN** the client opens the messages action
- **THEN** the application loads `GET /{id}/messages`
- **AND** displays the returned messages without exposing authentication data

#### Scenario: Client sends a message
- **GIVEN** the client has an active service request and a non-empty draft
- **WHEN** the client submits the draft
- **THEN** the application sends `POST /{id}/messages` with only `message_text` in the body
- **AND** appends the created message to the visible conversation