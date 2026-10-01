# Tasks: Perfil e Gestão de Veículos

## Fase 1: Infraestrutura de Estado
- [x] Adicionar campos de perfil (`user_profile_photo`, `user_full_name`, etc) ao `AppState`.
- [x] Adicionar lista `user_vehicles` e métodos de CRUD ao `OperationalState`.

## Fase 2: UI de Navegação
- [x] Criar componente `ProfileAvatar`.
- [x] Integrar `ProfileAvatar` no `customer_dashboard`.
- [x] Integrar `ProfileAvatar` no `provider_dashboard`.

## Fase 3: Tela de Perfil Unificada
- [x] Refatorar `/profile` para ser dinâmica com base no `user_role`.
- [x] Implementar componente de upload de foto com preview.
- [x] Implementar formulário de edição de dados básicos.

## Fase 4: CRUD de Veículos
- [x] Implementar seção "Meus Veículos" com listagem de cards.
- [x] Implementar modal de criação de veículo.
- [x] Implementar modal de edição de veículo.
- [x] Implementar funcionalidade de exclusão com confirmação.

## Fase 5: Verificação e Finalização
- [x] Verificar fluxo completo de perfil e veículos no papel de Cliente.
- [x] Verificar fluxo completo de perfil e veículos no papel de Prestador.
- [x] Marcar specs como implementadas (UI/Local) no OpenSpec.
