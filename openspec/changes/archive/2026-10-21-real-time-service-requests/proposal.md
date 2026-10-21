# Proposal: Real-time Service Requests Circuit

## Context
Previously, the provider dashboard relied on mock data. This change transforms the service request flow into a real-time system integrated with Xano.

## Objectives
Implement a complete circuit where:
1. Clients create service requests in Xano.
2. Providers automatically discover these pending requests via background polling.
3. Real-time data (user name, vehicle details, distance) is displayed on the provider's home screen.

## Technical Changes

### Backend (Xano)
- **Endpoint**: `/pending_requests` (GET)
- **Logic**: Query `service_requests` where `status == 'pendente'`.
- **Data Enrichment**: Join with `users` and `vehicles` tables to provide full context.

### Frontend (Reflex)
- **Polling Mechanism**: Implementation of `OperationalState.poll_pending_requests` using `@rx.event(background=True)` and `asyncio.sleep(20)`.
- **Data Mapping**: Transformation of raw Xano JSON (including nested `_user` and `_vehicle` objects) into UI-friendly formats.
- **UI Updates**: Dynamic rendering of the `available_requests` list on the provider home screen.
- **Session Sync**: Synchronization of `auth_token` between `AuthState` and `OperationalState` to prevent session expiration during polling.

## Verification
- Verify that a request created by a client appears on the provider's dashboard within 20 seconds.
- Confirm that the real name of the client (from the `users` table) is displayed.
- Ensure no session expiration occurs during active polling.
