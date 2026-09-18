# Spec: Provider Home (`/home_provider`)

## Description
Entry point for the collaborator/provider to manage availability and accept requests, then continue into a local/mock attendance flow.

## Provider Home Layout
- `rx.box` root with header + split body.
- Header: avatar + availability toggle (`OperationalState.is_available`).
- Split body:
    - Upper half: map (`provider-home-map`) initialized by `window.initSOSMap`.
    - Lower half: scrollable request list when available, or unavailable message.

## Request Card
- Shows icon, problem type, distance, user.
- Actions:
    - `Aceitar`: starts attendance flow and navigates to `/provider-service-progress`.
    - `Recusar`: removes request from local queue.

## Attendance In Progress (post-accept)

### Navigation
- On accept, `OperationalState.accept_request(id)` must:
    - store selected request in local state;
    - remove it from `available_requests`;
    - initialize mock attendance payload;
    - set initial phase to `A_CAMINHO`;
    - navigate to `/provider-service-progress`.

### Screen: `/provider-service-progress`
- Full-screen map reusing existing map infra (`window.initSOSMap`) plus route rendering between provider mock position and rescued user position.
- Fixed bottom card with rescued user data:
    - name;
    - problem type;
    - vehicle;
    - address;
    - observation.
- Distance and ETA shown as mock values from local state.

### Attendance phases (strict sequence)
- `A_CAMINHO` -> primary CTA `Cheguei ao local`.
- `NO_LOCAL` -> primary CTA `Iniciar atendimento`.
- `ATENDENDO` -> primary CTA `Concluir atendimento`.
- `CONCLUIDO` reached only after previous phases.

### Cancelation
- Secondary CTA `Cancelar atendimento` visible only in `A_CAMINHO` and `NO_LOCAL`.
- On cancel click, show confirmation modal: `Tem certeza que quer cancelar?`.
- If confirmed:
    - clear local attendance state;
    - navigate back to `/home_provider`;
    - request remains unavailable for this collaborator session (removed from list).

### Completion
- On `Concluir atendimento`, advance to `CONCLUIDO` and navigate to finalization screen (`/service-finalized`).

## Local/Mock State
- No Xano integration.
- State is local in `OperationalState` and centered around a helper builder function (mock payload setup).
- Required fields in `atendimento_mock`: id, nome, tipo_problema, veiculo, endereco, observacao, distance, eta, phone, maps_url, user_coords, provider_coords.

## Reuse constraints
- Reuse existing map stack and page components.
- Reuse existing avatar and button/card style tokens.
- Do not install new libraries.
