# Tasks: Home Screens Implementation

## Phase 1: State & Data Setup
- [x] Add `active_call_status` to `AppState`.
- [x] Add `is_available` and `available_requests` (mock list) to `OperationalState`.
- [x] Implement `accept_request` and `refuse_request` logic.

## Phase 2: User Home UI (`/home_client`)
- [x] Create `user_home_screen()` component.
- [x] Implement State A (Request Button) and State B (Active Call Card).
- [x] Implement Quick Access Grid.
- [x] Integrate with `profile_avatar()`.

## Phase 3: Provider Home UI (`/home_provider`)
- [x] Create `provider_home_screen()` component.
- [x] Implement Header with Availability Toggle.
- [x] Implement 50/50 Split layout.
- [x] Integrate Map in Upper half.
- [x] Implement Scrollable Request List in Lower half.
- [x] Implement `RequestCard` component.

## Phase 4: Routing & Integration
- [x] Update `home_screen()` to redirect to `/home_client` or `/home_provider` based on `user_role`.
- [x] Add pages to `app.add_page`.
- [ ] Test navigation flow: Login $\rightarrow$ Home $\rightarrow$ Map.
