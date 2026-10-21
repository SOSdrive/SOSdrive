## 1. Planning and schema

- [x] 1.1 Document the message and completion contracts in OpenSpec.
- [x] 1.2 Add the `service_messages` table with foreign keys and indexes.

## 2. Xano API

- [x] 2.1 Add authenticated `POST /service_requests/{id}/messages`.
- [x] 2.2 Add authenticated `PATCH /service_requests/{id}` with controlled completion.
- [x] 2.3 Preserve the legacy status route for releasing a request, restricting it to its assigned provider.

## 3. Verification

- [x] 3.1 Validate all changed XanoScript files.
- [x] 3.2 Published the Xano endpoint scripts in the target workspace; authenticated smoke tests still require client and provider sessions.

## 4. Reflex chat surface

- [x] 4.1 Add the authenticated GET messages endpoint and Python client helper.
- [x] 4.2 Connect the existing message action to a conversation panel with load, send, loading, and error states.
- [x] 4.3 Validate the Reflex module and XanoScript after the frontend integration.
- [x] 4.4 Add the client-side conversation panel for loading and sending messages on the active request.

## 5. Live conversation and participant authorization

- [x] 5.1 Add nullable `provider_id` to service requests and an authenticated acceptance endpoint that assigns the current provider only to pending requests.
- [x] 5.2 Restrict message GET and POST to the request owner or assigned provider, including rejection of non-participants.
- [x] 5.3 Poll the active conversation every 2 seconds while its panel is open; replace messages without duplicates and stop on close/request change.
- [x] 5.4 Preserve visible messages on transient poll failures and expose an accessible retry/status indication.
- [ ] 5.5 Make provider assignment atomic under concurrent acceptance attempts and verify that at most one provider is reported as successful.

## 6. Verification

- [x] 6.1 Add unit tests for polling lifecycle, incoming message updates, deduplication, and transient failures.
- [x] 6.2 Add focused frontend component tests for both provider and client chat panels.
- [x] 6.3 Add an opt-in Xano integration test for provider assignment and participant message authorization.
- [x] 6.4 Run the Python test suite and Reflex compile.
- [ ] 6.5 Run authenticated Xano integration checks with client and provider accounts (the endpoint scripts are published).
- [ ] 6.6 Verify the live chat in authenticated client and provider browser sessions, including delivery timing and polling shutdown.