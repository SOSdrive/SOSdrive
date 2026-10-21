# Spec: Gestão de Veículos

## Visão Geral
Define a funcionalidade de CRUD de veículos vinculados ao usuário/colaborador.

## Modelo de Dados (Local)
Um veículo é composto por:
- `id`: Identificador único.
- `brand`: Marca (ex: Toyota).
- `model`: Modelo (ex: Corolla).
- `plate`: Placa (ex: ABC-1234).
- `year`: Ano de fabricação.
- `color`: Cor.

## Cenários Funcionais

### Listagem de Veículos
**Given** que o usuário está na tela de perfil
**When** a seção "Meus Veículos" é renderizada
**Then** o sistema deve listar todos os veículos presentes em `OperationalState.user_vehicles`.
**Then** cada veículo deve ser exibido em um card com suas informações principais.

### Adição de Veículo
**Given** que o usuário clica em "Adicionar Veículo"
**When** o formulário de cadastro é preenchido e enviado
**Then** um novo veículo deve ser adicionado ao array local com um ID incremental.
**Then** o formulário deve ser fechado e a lista atualizada.

### Edição de Veículo
**Given** que o usuário clica em "Editar" em um veículo existente
**When** os dados são alterados e salvos
**Then** o veículo correspondente no array local deve ser atualizado.

### Exclusão de Veículo
**Given** que o usuário clica em "Excluir" em um veículo
**When** o usuário confirma a exclusão
**Then** o veículo deve ser removido do array local.

## Regras de Validação
- A placa do veículo é obrigatória.
- Marca e Modelo são obrigatórios.
- O ano deve ser um número válido.

---
**Status: Implementado (UI/Estado Local)**
Integração com backend (Xano) prevista para etapa futura.

