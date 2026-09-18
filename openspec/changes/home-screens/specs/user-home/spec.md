# Spec: User Home (`/home_client`)

## Description
The central hub for the client. It handles the transition between "idle" and "active request" states.

## Component Hierarchy
- `rx.box` (Root, background white, width 100%, min_height 100vh)
    - `rx.vstack` (Container, centered, max_width 600px)
        - `rx.hstack` (Header: Avatar at the end)
        - `rx.cond` (State Switch)
            - **Case A (No active call)**: `rx.button` ("Solicitar Socorro", Primary, Large, centered)
            - **Case B (Active call)**: `rx.vstack` (Status Card: Text "Chamado em andamento", ETA, Button "Acompanhar")
        - `rx.grid` (Quick Access: 3 columns)
            - Card: "Meus Veículos" $\rightarrow$ `/profile`
            - Card: "Histórico" $\rightarrow$ `/history` (mock)
            - Card: "Perfil" $\rightarrow$ `/profile`

## State Management
- `AppState.active_call_status`:
    - `None`: Render State A.
    - `"searching"` or `"matched"`: Render State B.
- `on_click` for Request button: `rx.redirect("/customer")`.
- `on_click` for Track button: `rx.redirect("/customer")`.

## Styling
- Button: `width="100%"`, `height="12rem"`, `border_radius="24px"`, `background=COLORS['emergency_orange']`.
- Quick Access Cards: `class_name="op-card"`, `padding="1rem"`, `aspect_ratio="1/1"`.
