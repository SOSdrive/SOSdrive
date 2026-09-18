# Proposal: Home Screens for User and Provider

## Context
The application currently has operational dashboards (map-focused), but lacks a central "Home" hub for both user roles. Users need a clear entry point to request help, and providers need a way to manage their availability and view available requests before entering navigation mode.

## Objectives
- Create a dedicated Home for the User (Client) that prioritizes the "Request Help" action and manages the transition to active calls.
- Create a dedicated Home for the Provider that manages availability and lists available requests.
- Ensure the transition from Login $\rightarrow$ Home is seamless based on the `user_role`.
- Maintain 100% UI/Local state mocking for now.

## Proposed Changes
1. **User Home (`/home_client`)**:
    - Central "Request Help" button (State A).
    - "Active Call" status card with ETA and "Track" button (State B).
    - Quick access grid: Vehicles, History, Profile.
2. **Provider Home (`/home_provider`)**:
    - Availability Toggle (On/Off).
    - 50/50 Split Layout: Top map (nearby requests) / Bottom list (request details).
    - Request actions: Accept (navigates to operational map) or Refuse.
3. **Navigation Update**: Update `/home` redirect logic to target these new specific home screens.
