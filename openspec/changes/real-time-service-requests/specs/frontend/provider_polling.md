# Spec: Provider Real-time Dashboard

## Functionality
The provider home screen must dynamically update a list of available service requests without requiring a page refresh.

## Implementation Details

### Polling Logic
- **Trigger**: `on_mount` of `provider_home_screen` and `provider_dashboard`.
- **Mechanism**: `OperationalState.poll_pending_requests` runs in the background.
- **Interval**: 20 seconds.
- **Sequence**: Immediate first call $\rightarrow$ `asyncio.sleep(20)` $\rightarrow$ Repeat.

### Data Mapping
Raw Xano data is mapped to UI state using `_map_xano_to_ui_request`:
- **User Identity**: Priority check for `_user.name` $\rightarrow$ `user_name` $\rightarrow$ `name`.
- **Vehicle Info**: Priority check for `_vehicle.details` $\rightarrow$ `vehicle_details` $\rightarrow$ `vehicle`.
- **Distance**: Calculated using the Haversine formula between the provider's current GPS coordinates and the request coordinates.

### UI Components
- **Request Card**: Displays service icon, friendly service name, client name, distance, and an "Accept" button.
- **Availability Toggle**: Providers must be "Online" to have the polling active and visible.
