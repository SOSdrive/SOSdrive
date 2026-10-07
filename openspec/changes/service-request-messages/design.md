## Context

O repositório já possui o grupo Xano `Service Requests`, a tabela `service_request` e um endpoint legado `POST /update_request_status`. Não há tabela de mensagens nem rota REST com parâmetro de caminho.

## Goals / Non-Goals

**Goals:**

- Manter o padrão XanoScript já usado no projeto.
- Garantir relação 1:N por foreign key `service_request_id`.
- Aplicar autenticação e validação de existência no backend.
- Permitir somente `accepted` ou `in_progress` como estados de origem para `completed`.

**Non-Goals:**

- Não alterar componentes Reflex ou adicionar polling de mensagens.
- Não substituir o endpoint legado usado pelo cliente atual.
- Não introduzir dependências ou tecnologias novas.

## Decisions

- Usar o nome físico `service_messages`, conforme solicitado; a foreign key aponta para a tabela real `service_request` existente no workspace, e a API usa o caminho plural solicitado.
- Criar `service_request_id` com `table = "service_request"` e índice btree composto com `created_at`, permitindo várias mensagens por chamado e consulta ordenada.
- Usar `$auth.id` para `sender_id`; o cliente nunca poderá escolher outro remetente.
- Validar `message_text` com `trim` e precondition não vazia antes de `db.add`.
- No PATCH, buscar o chamado e aceitar `completed` somente quando o status atual for `accepted` ou `in_progress`; outros status retornam `accessdenied`.

## Risks / Trade-offs

- **[Risco]** O endpoint legado aceita qualquer status. **Mitigação:** o novo contrato PATCH aplica a transição controlada sem quebrar o contrato existente; a restrição global pode ser migrada depois.
- **[Risco]** A tabela física singular pode divergir do nome informal `service_messages`. **Mitigação:** documentar o mapeamento e manter o caminho HTTP plural pedido.
- **[Risco]** A criação em Xano depende de aplicar os arquivos no workspace correto. **Mitigação:** validar XanoScript localmente e executar smoke tests autenticados após publicação.

## Migration Plan

1. Validar os arquivos XanoScript novos e modificados.
2. Aplicar a tabela `service_message` no workspace Xano.
3. Publicar os endpoints no grupo `Service Requests`.
4. Testar criação de mensagem e transição `accepted`/`in_progress` para `completed` com token válido.
5. Para rollback, despublicar as rotas novas e remover a tabela somente após confirmar ausência de dependências.