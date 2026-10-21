## MODIFIED Requirements

### Requirement: Provider can manage availability from provider home
The provider home screen MUST show the Prestador's current availability state
with a clear, accessible control to switch between available and unavailable.
The screen MUST keep nearby requests visible only while available.

#### Scenario: Prestador goes online
- **GIVEN** the Prestador is on `/home_provider` and is unavailable
- **WHEN** the Prestador activates the availability control
- **THEN** the state changes to available
- **AND** the screen clearly indicates "Disponível"
- **AND** nearby requests are shown

#### Scenario: Prestador goes offline
- **GIVEN** the Prestador is on `/home_provider` and is available
- **WHEN** the Prestador activates the availability control
- **THEN** the state changes to unavailable
- **AND** the screen clearly indicates "Indisponível"
- **AND** nearby requests are hidden

#### Scenario: Availability control is used with assistive technology
- **GIVEN** the Prestador navigates the home screen using keyboard or assistive
  technology
- **WHEN** the Prestador reaches the availability control
- **THEN** the control exposes its purpose and current state through an
  accessible label
- **AND** it can be activated without relying on color alone

### Requirement: Provider can center the home map on their current location
The provider home screen MUST initialize and center its map on the Prestador's
current browser-provided location when available. It MUST provide an explicit
action to recenter the map on that location after the map has been moved or
zoomed.

#### Scenario: Location is available when provider home opens
- **GIVEN** browser geolocation is available and permission is granted
- **WHEN** `/home_provider` initializes its map
- **THEN** the map is centered on the Prestador's current coordinates
- **AND** a marker identifies the Prestador's location

#### Scenario: Prestador recenters after moving the map
- **GIVEN** the Prestador has panned or zoomed away from their position
- **WHEN** the Prestador activates "Centralizar no meu local"
- **THEN** the map returns to the most recently obtained current coordinates
- **AND** the Prestador's location marker is visible

#### Scenario: Geolocation is denied or unavailable
- **GIVEN** browser geolocation is denied, unavailable, or returns an error
- **WHEN** the map initializes or the Prestador requests recentering
- **THEN** the map remains usable with its default center
- **AND** the screen communicates that current location could not be obtained
- **AND** the Prestador can retry using the recenter action
