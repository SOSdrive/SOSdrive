## Why

Chamados aceitos precisam registrar mensagens entre motorista e prestador, e o fluxo atual ainda não oferece persistência para essa comunicação. A conclusão do atendimento também precisa ser representada explicitamente no endpoint REST de status.

## What Changes

- Criar a tabela `service_message` com referência 1:N a `service_request`.
- Adicionar `POST /service_requests/{id}/messages` para criar mensagens autenticadas.
- Derivar `sender_id` do usuário autenticado e validar a existência do chamado no backend.
- Adicionar o contrato `PATCH /service_requests/{id}` para permitir a transição para `completed` a partir de `accepted` ou `in_progress`.
- Preservar o endpoint legado `POST /update_request_status` para não quebrar o cliente Reflex atual.

## Capabilities

### New Capabilities

- `service-request-messages`: Persistência e criação autenticada de mensagens de chamados.

### Modified Capabilities

- `service-request-status`: Atualização REST de status com conclusão controlada.

## Impact

- **Xano**: nova tabela, novo endpoint POST e novo endpoint PATCH no grupo `Service Requests`.
- **Domínio**: amplia a entidade Chamado; cada mensagem pertence a um Chamado e a um usuário remetente.
- **Autorização**: permanece no Xano, usando o token atual e `$auth.id`; não há alteração visual nem de lógica do frontend.
- **Rollback**: remover os endpoints novos e a tabela `service_message`; o endpoint legado continua disponível.