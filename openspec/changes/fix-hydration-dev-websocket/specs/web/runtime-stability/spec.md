## Purpose

Defines the browser-rendering and development-server behavior needed to keep the Reflex application hydrated correctly and reliably connected during local development.

## ADDED Requirements

### Requirement: Server-rendered documents use valid HTML structure
The application MUST render document head and body content with valid HTML nesting so React can hydrate the server-rendered page without structural mismatch warnings.

#### Scenario: Application route hydrates
- **WHEN** a user opens any application route
- **THEN** the browser receives valid document head and body markup
- **AND** React hydrates the page without an invalid head-child or hydration-mismatch error

### Requirement: Browser-only features initialize after client mounting
The application MUST defer browser-dependent initialization until the browser APIs and required client-side libraries are available, without changing the server-rendered page structure.

#### Scenario: A page initializes a browser-dependent feature
- **WHEN** the page has mounted in the browser
- **THEN** browser-only helpers initialize after their required libraries are available
- **AND** the feature remains usable without introducing hydration mismatches

### Requirement: Development hot reload uses the active application endpoint
The development frontend MUST establish its hot-reload WebSocket connection using the active development host and frontend port, and the Reflex client MUST connect to the active backend endpoint.

#### Scenario: Development server runs on configured ports
- **GIVEN** the frontend and backend are started on configured development ports
- **WHEN** the development page loads
- **THEN** the HMR and application WebSocket connections target the active host and corresponding ports
- **AND** the browser console reports no connection-refused error for a stale or inactive port

### Requirement: Development services report readiness
The local development workflow MUST make it possible to verify that the frontend and backend are listening on their configured ports before browser testing.

#### Scenario: Developer verifies service readiness
- **WHEN** the local development app starts successfully
- **THEN** the frontend and backend accept connections on their configured ports
- **AND** the documented verification can distinguish an active service from a port conflict or unavailable service
