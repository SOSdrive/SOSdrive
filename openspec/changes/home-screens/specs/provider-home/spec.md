# Spec: Provider Home (`/home_provider`)

## Description
The entry point for the provider to manage availability and accept requests.

## Component Hierarchy
- `rx.box` (Root, width 100%, height 100vh, overflow hidden)
    - `rx.hstack` (Header: Avatar + Availability Toggle Switch)
    - `rx.vstack` (Main Body, height="calc(100vh - 4rem)")
        - `rx.box` (Upper Half: Map, height="50%", width="100%", id="provider-home-map")
        - `rx.box` (Lower Half: List, height="50%", width="100%", overflow_y="auto", padding="1rem")
            - `rx.cond` (Availability check)
                - **If Available**: `rx.foreach` over `OperationalState.available_requests` $\rightarrow$ `RequestCard`
                - **If Unavailable**: `rx.center` $\rightarrow$ `rx.text("Você está indisponível para novos chamados")`

## RequestCard Component
- `rx.hstack` (White background, border, border_radius 12px, padding 1rem)
    - `rx.vstack` (Left: Problem Type (Bold), Distance, User Name)
    - `rx.spacer()`
    - `rx.hstack` (Right: Button "Aceitar" (Primary), Button "Recusar" (Secondary))

## State Management
- `OperationalState.is_available`: Boolean toggle.
- `OperationalState.available_requests`: List of dicts `{"id", "type", "distance", "user"}`.
- `accept_request(id)`:
    - Remove request from list.
    - `rx.redirect("/provider")`.
- `refuse_request(id)`:
    - Remove request from list.

## Map Logic
- `on_mount`: Initialize map using `window.initSOSMap`.
- Display static mock pins based on `available_requests` coords.
