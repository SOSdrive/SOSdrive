# Design: Perfil e Gestão de Veículos

## Arquitetura de Componentes
- `ProfileAvatar`: Componente reutilizável para o header.
- `ProfileEditor`: Formulário de edição de dados básicos e foto.
- `VehicleManager`: Seção de listagem e CRUD de veículos.
- `VehicleForm`: Modal para criação e edição de veículos.

## Estrutura de Estado (Mock)
### AppState
- `user_profile_photo`: string (URL ou base64).
- `user_full_name`: string.
- `user_email`: string.
- `user_phone`: string.

### OperationalState
- `user_vehicles`: list[dict] (Lista de veículos do usuário logado).
  - `id`: int
  - `brand`: string
  - `model`: string
  - `plate`: string
  - `year`: int
  - `color`: string

## Fluxo de Dados
1. **Upload de Foto**: O componente de upload converterá a imagem para base64 e atualizará `AppState.user_profile_photo`.
2. **Gestão de Veículos**: Operações de `add_vehicle`, `update_vehicle` e `delete_vehicle` manipularão a lista `OperationalState.user_vehicles`.

## Reuso e Padrões
- Utilizar as cores definidas em `styles.py`.
- Manter a consistência visual com os cards e inputs já presentes no projeto.
- A tela `/profile` será dinâmica, exibindo campos específicos baseados em `AppState.user_role`.
