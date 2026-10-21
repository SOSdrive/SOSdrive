## ADDED Requirements

### Requirement: A service request has many messages
The system MUST persist zero or more messages for each service request, and each message MUST belong to exactly one service request.

#### Scenario: Message relationship
- **GIVEN** a service request exists
- **WHEN** one or more messages are created for it
- **THEN** every message stores the request identifier in `service_request_id`
- **AND** querying by `service_request_id` returns all messages for that request

### Requirement: Authenticated users can create request messages
The system MUST expose `POST /service_requests/{id}/messages` with a `message_text` input and return the created message. Only the request's owning client and assigned provider may read or create messages.

#### Scenario: Create message
- **GIVEN** a valid authenticated user and an existing service request
- **WHEN** the user submits non-empty `message_text`
- **THEN** the API creates one message with the URL request id and `$auth.id` as `sender_id`
- **AND** returns the created record
- **AND** records the authenticated user as `sender_id`

#### Scenario: Assigned provider sends a message
- **GIVEN** the authenticated provider accepted the service request
- **WHEN** the provider submits non-empty `message_text`
- **THEN** the message is persisted with the provider's authenticated user id

#### Scenario: Non-participant cannot create a message
- **GIVEN** an authenticated user is neither the request's owning client nor its assigned provider
- **WHEN** the user submits a message
- **THEN** the API rejects the request and creates no message

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
The system MUST expose `GET /service_requests/{id}/messages` and return the messages for the requested service request in creation order only to its owning client or assigned provider.

#### Scenario: Load conversation
- **GIVEN** a valid authenticated user and an existing service request
- **WHEN** the client requests the conversation
- **THEN** the API returns the request messages ordered from oldest to newest
- **AND** the client can render the message text and sender identifier

#### Scenario: Non-participant cannot read a conversation
- **GIVEN** an authenticated user is neither the request's owning client nor its assigned provider
- **WHEN** the user requests the conversation
- **THEN** the API rejects the request without returning message content

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

#### Scenario: Provider sends a message
- **GIVEN** the provider has accepted the client's active service request
- **WHEN** the provider opens the conversation and sends a non-empty message
- **THEN** the application persists and displays the message in the same request conversation

### Requirement: An open request conversation receives messages automatically
The client and provider applications MUST refresh the active conversation every 2 seconds while its panel is open, render messages from either participant without duplicates, and stop refreshing when the panel closes or the active request changes.

#### Scenario: Receive a message while the conversation is open
- **GIVEN** both participants have the same conversation open
- **WHEN** either participant sends a message
- **THEN** the other participant sees it within 2 seconds without closing or reloading the panel

#### Scenario: Temporarily unavailable message API
- **GIVEN** the conversation already displays messages
- **WHEN** a periodic refresh fails
- **THEN** the displayed messages remain visible and the client may retry on the next interval

#### Scenario: Conversation closes
- **GIVEN** the conversation panel is open and refreshing
- **WHEN** the user closes it or changes the active request
- **THEN** no further periodic message requests are made for the closed conversation

### Requirement: Service request acceptance assigns a provider
The system MUST persist the authenticated provider id when a provider accepts a pending request, and MUST NOT allow a non-provider or a second provider to take an already assigned request.

#### Scenario: Provider accepts a pending request
- **GIVEN** a pending request and an authenticated user with provider role
- **WHEN** the provider accepts it
- **THEN** the request stores that user's id as `provider_id` and changes to accepted

#### Scenario: Invalid user or request state attempts acceptance
- **GIVEN** an authenticated non-provider or a request that is not pending
- **WHEN** the user attempts acceptance
- **THEN** the API rejects it without changing the assignment or status

#### Scenario: Two providers accept concurrently
- **GIVEN** two authenticated providers attempt to accept the same pending request at the same time
- **WHEN** both acceptance requests are processed
- **THEN** exactly one provider is assigned
- **AND** the other acceptance request is rejected without overwriting the assigned provider
- **AND** a unique database index on `service_request_acceptance.service_request_id` arbitrates the concurrent claims

#### Scenario: A released request can be accepted again
- **GIVEN** the assigned provider releases the service request back to `pending`
- **WHEN** another provider accepts the request
- **THEN** the request is assigned to the new provider
- **AND** the previous acceptance reservation no longer blocks acceptance