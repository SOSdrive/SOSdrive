## Why

Chamados aceitos precisam registrar mensagens entre motorista e prestador, e o fluxo atual ainda não oferece persistência para essa comunicação. A conclusão do atendimento também precisa ser representada explicitamente no endpoint REST de status.

## What Changes

- Criar a tabela `service_message` com referência 1:N a `service_request`.
- Adicionar `POST /service_requests/{id}/messages` para criar mensagens autenticadas.
- Derivar `sender_id` do usuário autenticado e permitir acesso apenas ao cliente dono do chamado e ao prestador atribuído.
- Registrar no chamado o prestador autenticado que o aceitou e proteger a atribuição no backend.
- Atualizar a conversa aberta automaticamente a cada 2 segundos, sem duplicar mensagens e sem polling quando o painel estiver fechado.
- Adicionar o contrato `PATCH /service_requests/{id}` para permitir a transição para `completed` a partir de `accepted` ou `in_progress`.
- Preservar a rota legada `POST /update_request_status` para liberar um chamado ao cancelá-lo, restringindo a ação ao prestador atribuído e à transição para `pending`.

## Capabilities

### New Capabilities

- `service-request-messages`: Persistência e criação autenticada de mensagens de chamados.

### Modified Capabilities

- `service-request-status`: Atualização REST de status com conclusão controlada.

## Impact

- **Xano**: vínculo do prestador no chamado, endpoints autenticados de aceite e autorização nas rotas de mensagens; a rota legada de status continua disponível somente para liberar o chamado do prestador atribuído.
- **Domínio**: amplia a entidade Chamado; cada mensagem pertence a um Chamado e a um usuário remetente.
- **Autorização**: permanece no Xano, usando o token atual e `$auth.id`; a conversa aberta consulta o endpoint existente em intervalo curto para refletir mensagens de ambos os participantes.
- **Frontend**: atualiza a lista ao vivo somente enquanto a conversa estiver aberta e preserva mensagens carregadas em caso de falha temporária de rede.
- **Rollback**: remover os endpoints novos e a tabela `service_message`; a rota legada permanece disponível com a validação de autorização para liberação do chamado.