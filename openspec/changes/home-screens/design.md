# Design: Home Screens

## Visual Identity
- Follow the existing `styles.py` (COLORS, GLOBAL_STYLE).
- Use `rx.center` for layout centering on desktop.
- Primary color for the "Request Help" button to ensure high visibility.
- Glass-panel effects for secondary cards and headers.

## User Home Layout
- **Header**: Fixed top, containing the `profile_avatar()`.
- **Center Area**:
    - **State A**: Huge circular or rounded-rect button "Solicitar Socorro" (Primary Color).
    - **State B**: Card with background white, border `COLORS['emergency_orange']`, showing "Chamado em andamento" and a "Acompanhar" button.
- **Footer Grid**: 3 columns of cards (Vehicles, History, Settings).

## Provider Home Layout
- **Header**: `profile_avatar()` and a `rx.switch` or toggle button for Availability.
- **Split View**:
    - **Upper (50vh)**: Full-width map utilizing existing Leaflet wrapper.
    - **Lower (50vh)**: Scrollable `rx.vstack` containing `RequestCard` components.
- **RequestCard**:
    - Horizontal layout: [Icon | Text Details] [Accept Button | Refuse Button].
    - White background, `COLORS['line']` border.

## Interaction Flow
1. Login $\rightarrow$ check `AppState.user_role`.
2. If `client` $\rightarrow$ `/home_client`.
3. If `provider` $\rightarrow$ `/home_provider`.
4. User Home $\rightarrow$ Request $\rightarrow$ `/customer` (Map/Service Selection).
5. Provider Home $\rightarrow$ Accept $\rightarrow$ `/provider` (Operational Map).
