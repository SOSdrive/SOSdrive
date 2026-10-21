# Proposal: Perfil e Gestão de Veículos (UI/Local)

## Objetivo
Implementar a interface de perfil de usuário e colaborador, incluindo um avatar circular de navegação e a gestão completa (CRUD) de veículos, operando exclusivamente com estado local para posterior integração com Xano.

## Escopo
- **Avatar de Perfil**: Ícone circular no canto superior dos dashboards.
- **Edição de Perfil**: Tela unificada de edição de dados pessoais e upload de foto com preview.
- **Gestão de Veículos**: CRUD completo de veículos disponível para ambos os perfis.
- **Contextos**: Implementação funcional tanto para o perfil de 'Cliente' quanto para o de 'Prestador'.

## Alinhamento com MVP
Esta funcionalidade é fundamental para a experiência do usuário e a operação do serviço de socorro veicular, permitindo que o sistema saiba quais veículos estão vinculados a qual conta.

## Impacto no Domínio
- **Motorista (Cliente)**: Ganha a capacidade de gerir seus dados e veículos.
- **Prestador (Colaborador)**: Ganha a capacidade de gerir seus dados e veículos.

## Estratégia de Implementação
A lógica de manipulação de dados será isolada em métodos do estado do Reflex (`AppState` e `OperationalState`), facilitando a substituição futura por chamadas de API.
