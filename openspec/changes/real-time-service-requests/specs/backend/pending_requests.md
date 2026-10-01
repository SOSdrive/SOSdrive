# Spec: Pending Requests API Integration

## Endpoint Definition
- **Path**: `/pending_requests`
- **Method**: `GET`
- **Authentication**: Required (Bearer Token)

## Database Logic
- **Primary Table**: `service_requests`
- **Filter**: `status == 'pendente'`
- **Joins**:
  - `users` table via `user_id` (Retrieve `name`, `phone`)
  - `vehicles` table via `vehicle_id` (Retrieve `brand`, `model`, `plate`)

## Expected Response Format
The API must return a list of objects containing:
- `id`: Request ID
- `service_type`: Type of service (e.g., 'tire', 'battery')
- `user_name`: Name of the client
- `user_phone`: Client's phone number
- `vehicle_details`: Combined brand, model, and plate
- `latitude` / `longitude`: Request coordinates
- `address`: Full address
- `note`: Additional observations
- `status`: Must be 'pending'/'pendente'
