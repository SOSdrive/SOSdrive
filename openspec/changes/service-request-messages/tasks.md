## 1. Planning and schema

- [x] 1.1 Document the message and completion contracts in OpenSpec.
- [x] 1.2 Add the `service_messages` table with foreign keys and indexes.

## 2. Xano API

- [x] 2.1 Add authenticated `POST /service_requests/{id}/messages`.
- [x] 2.2 Add authenticated `PATCH /service_requests/{id}` with controlled completion.
- [x] 2.3 Preserve the existing legacy status endpoint for compatibility.

## 3. Verification

- [x] 3.1 Validate all changed XanoScript files.
- [x] 3.2 Documented the external Xano credentials/environment blocker; authenticated smoke tests remain to be run after publication.

## 4. Reflex chat surface

- [x] 4.1 Add the authenticated GET messages endpoint and Python client helper.
- [x] 4.2 Connect the existing message action to a conversation panel with load, send, loading, and error states.
- [x] 4.3 Validate the Reflex module and XanoScript after the frontend integration.
- [x] 4.4 Add the client-side conversation panel for loading and sending messages on the active request.