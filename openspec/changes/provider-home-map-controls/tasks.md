## 1. Prestador availability

- [x] 1.1 (frontend Reflex; reuse existing `OperationalState.is_available`) Refine
  the provider-home availability control so its state and action are explicit,
  accessible, and visible on mobile and desktop.
- [x] 1.2 (frontend Reflex; reuse existing request list) Preserve state-driven
  nearby request visibility and verify the status label/visual treatment updates
  immediately after toggling.

## 2. Provider map location controls

- [x] 2.1 (frontend/map; reuse existing Leaflet and browser geolocation) On
  provider-home map initialization, obtain current coordinates when permitted,
  add/update a Prestador marker, and center the map there.
- [x] 2.2 (frontend/map; reuse existing map wrapper) Add an explicit
  "Centralizar no meu local" action that requests current coordinates and
  recenters after map pan/zoom.
- [x] 2.3 (frontend Reflex; reuse existing feedback styles) Handle denied,
  unavailable, and failed geolocation with safe feedback, default map fallback,
  and a working retry action.
- [ ] 2.4 (frontend; reuse existing layout styles) Verify controls do not
  obstruct map interactions or the request list on mobile and desktop.

## 3. Verification

- [ ] 3.1 Add focused tests or a documented manual verification for online/offline
  transitions, map initialization/recenter, geolocation failure and retry.
- [x] 3.2 Run relevant tests and Reflex backend validation; do not add Xano persistence
  or change authorization as part of this change.
