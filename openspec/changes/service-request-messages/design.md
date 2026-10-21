## Context

O repositório já possui o grupo Xano `Service Requests`, a tabela `service_request` e um endpoint legado `POST /update_request_status`. Não há tabela de mensagens nem rota REST com parâmetro de caminho.

## Goals / Non-Goals

**Goals:**

- Manter o padrão XanoScript já usado no projeto.
- Garantir relação 1:N por foreign key `service_request_id`.
- Aplicar autenticação, vínculo de participantes e validação de existência no backend.
- Permitir somente `accepted` ou `in_progress` como estados de origem para `completed`.
- Atualizar a conversa aberta a cada 2 segundos usando o GET autenticado existente.

**Non-Goals:**

- Não expor transições de status arbitrárias pelo endpoint legado.
- Não atribuir prestador por meio do cliente ou do endpoint genérico de status.
- Não introduzir dependências ou tecnologias novas.
- Não manter polling quando o painel estiver fechado nem implementar sincronização offline.

## Decisions

- Usar o nome físico `service_messages`, conforme solicitado; a foreign key aponta para a tabela real `service_request` existente no workspace, e a API usa o caminho plural solicitado.
- Criar `service_request_id` com `table = "service_request"` e índice btree composto com `created_at`, permitindo várias mensagens por chamado e consulta ordenada.
- Usar `$auth.id` para `sender_id`; o cliente nunca poderá escolher outro remetente.
- Acrescentar `provider_id` opcional a `service_request`. Um endpoint autenticado de aceite deve aceitar apenas chamados pendentes por um usuário com papel `prestador`, gravando `$auth.id` como `provider_id`.
- Registrar primeiro a tentativa de aceite em `service_request_acceptance`, com índice único em `service_request_id`; a restrição do banco escolhe um único vencedor mesmo sob requisições concorrentes. Só depois de inserir a reserva, atualizar o chamado e responder sucesso. Ao liberar um chamado, remover a reserva correspondente para que possa ser aceito novamente.
- Restringir GET e POST de mensagens ao usuário `service_request.user_id` ou ao `service_request.provider_id`; papel de prestador, sozinho, não autoriza acesso.
- Validar `message_text` com `trim` e precondition não vazia antes de `db.add`.
- Enquanto o painel estiver aberto, buscar mensagens pelo endpoint GET a cada 2 segundos. Substituir a lista pelo resultado ordenado do servidor para evitar duplicação e incluir mensagens recebidas do outro participante. Parar a consulta ao fechar ou trocar o chamado; falha temporária não deve apagar mensagens já exibidas.
- No PATCH, buscar o chamado e aceitar `completed` somente quando o status atual for `accepted` ou `in_progress`; outros status retornam `accessdenied`.

## Risks / Trade-offs

- **[Risco]** Clientes externos podem depender das transições arbitrárias do endpoint legado. **Mitigação:** manter a rota para a liberação pelo prestador atribuído e publicar o novo endpoint de aceite; as transições genéricas deixam de ser aceitas.
- **[Risco]** A tabela física singular pode divergir do nome informal `service_messages`. **Mitigação:** documentar o mapeamento e manter o caminho HTTP plural pedido.
- **[Risco]** A criação em Xano depende de aplicar os arquivos no workspace correto. **Mitigação:** validar XanoScript localmente e executar smoke tests autenticados após publicação.
- **[Risco]** Polling frequente aumenta leituras enquanto a conversa está aberta. **Mitigação:** usar intervalo de 2 segundos apenas no painel aberto e encerrar o loop ao fechá-lo.
- **[Risco]** Chamados existentes podem não ter prestador atribuído. **Mitigação:** bloquear o acesso do prestador a esses chamados até que sejam aceitos pelo novo endpoint.
- **[Risco]** A leitura e atualização do chamado são operações separadas. **Mitigação:** reservar o chamado numa tabela com restrição única por chamado antes de atualizar `provider_id`; um conflito de unicidade não pode ser tratado como sucesso.

## Migration Plan

1. Validar os arquivos XanoScript novos e modificados.
2. Aplicar a alteração da tabela `service_request` e a tabela `service_message` no workspace Xano.
3. Publicar o endpoint de aceite e publicar os endpoints de mensagens com autorização por participante.
4. Testar aceite, leitura e criação de mensagens por cliente, prestador atribuído e usuário não participante.
5. Verificar que a conversa aberta recebe novas mensagens em até 2 segundos e encerra o polling ao fechar.
6. Para rollback, despublicar as rotas novas e remover as alterações de schema somente após confirmar ausência de dependências.