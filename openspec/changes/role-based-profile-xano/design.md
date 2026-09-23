## Context

O fluxo atual em `sosdrive.py` já mantém sessão Reflex, chama `auth/login` e consulta `auth/me`; o Xano também possui a tabela `user` com role `client`/`provider`. A nova capacidade precisa alinhar esses valores ao vocabulário do produto (`cliente`/`prestador`), adicionar dados cadastrais separados e preservar a autorização no backend.

A motivação e o comportamento observável estão em `proposal.md` e nas especificações desta mudança. O design deve reutilizar o estado de autenticação, os tokens de estilo em `styles.py` e os endpoints Xano existentes.

## Goals / Non-Goals

**Goals:**

- Normalizar a role no contrato de autenticação e usar a role validada pelo backend para o redirecionamento.
- Criar um modelo `user_profile` um-para-um com `user`, com leitura e gravação autenticadas.
- Reutilizar a tela/formulário de autenticação e os componentes de entrada existentes, adicionando máscaras de CPF e telefone sem alterar o valor canônico enviado à API.
- Manter o mesmo sistema visual responsivo em `/perfil-cliente` e `/perfil-prestador`.
- Garantir validação de propriedade no Xano a partir do sujeito do token.

**Non-Goals:**

- Não alterar chamados, avaliações, localização, disponibilidade ou dashboards operacionais.
- Não adicionar pagamentos, histórico avançado, login social ou uma nova tecnologia de frontend.
- Não permitir edição da role pelo formulário de perfil.

## Decisions

### Role canônica e compatibilidade de dados

A API e o código Python usarão `cliente` e `prestador` como valores canônicos. A migração Xano converterá registros existentes `client` para `cliente` e `provider` para `prestador` antes de restringir o enum. O backend rejeitará qualquer outro valor; o frontend não poderá contornar essa validação.

Alternativa considerada: manter `client`/`provider` internamente e traduzir apenas na interface. Foi rejeitada porque deixaria o contrato do domínio inconsistente e permitiria novos registros com vocabulário diferente.

### Contrato de login e carregamento da sessão

O `POST /auth/login` continuará retornando `authToken` e `user_id`, acrescentando `role` ou garantindo que a consulta subsequente `GET /auth/me` retorne a role canônica. O cliente considerará a resposta de `auth/me` como fonte final para o redirecionamento, evitando confiar em um valor de role enviado por estado de rota.

Alternativa considerada: guardar a role somente no navegador. Foi rejeitada porque a autorização deve permanecer no servidor e a sessão já é mantida pelo estado Reflex.

### Modelo e endpoints de perfil

Será criada a tabela `user_profile` com `id`, `user_id` (referência para `user` e índice único), `nome_completo`, `cpf`, `telefone` e `foto_perfil`. `GET /user_profile` retornará o registro ligado a `$auth.id`; `POST /user_profile` criará o registro quando ausente e `PUT /user_profile` atualizará o registro existente. Ambos ignorarão ou rejeitarão `user_id` fornecido pelo cliente e usarão o ID do token.

Alternativa considerada: colocar esses campos diretamente em `user`. Foi rejeitada para separar credenciais/autorização dos dados cadastrais e permitir evolução do perfil sem ampliar a tabela de autenticação.

### Autorização e integridade

Os endpoints Xano terão autenticação de usuário habilitada, buscarão o perfil por `user_id = $auth.id` e aplicarão a unicidade no banco. O backend também validará CPF/telefone conforme o contrato e limitará a foto a uma URL ou formato aceito pelo storage configurado. O Reflex exibirá erros seguros, mas não será responsável por autorização.

### Frontend e padrão visual

As duas rotas de perfil reutilizarão um componente comum com uma propriedade de role/título, o estado `AuthState` existente e os tokens de `styles.py`. O formulário manterá valores editáveis localmente, formatará CPF/telefone para exibição e enviará os valores normalizados. O upload usará o mecanismo de upload já disponível no Reflex; se o storage Xano ainda não estiver configurado, a URL de foto será tratada como campo opcional e o restante do perfil continuará utilizável.

Alternativa considerada: duas implementações independentes. Foi rejeitada porque aumentaria divergência visual e duplicação de validação.

## Risks / Trade-offs

- **[Role legada]** Registros existentes usam `client`/`provider` → executar migração explícita e validar contagem antes de restringir o enum.
- **[Perfil ausente]** Usuários atuais podem não ter linha em `user_profile` → `GET` retornará estado vazio controlado e o `POST` fará criação idempotente para o usuário autenticado.
- **[Upload]** O storage de imagem pode não estar disponível em todos os ambientes → tratar `foto_perfil` como opcional e mostrar erro específico sem impedir salvar os campos textuais.
- **[Dados pessoais]** CPF e telefone são sensíveis → não registrar valores em logs, usar HTTPS no endpoint configurado e impedir acesso cruzado pelo backend.
- **[Contrato duplicado]** A role pode aparecer em login e `auth/me` → validar consistência e usar `auth/me` como fonte final antes de redirecionar.

## Migration Plan

1. Adicionar e validar a estrutura `user_profile` com referência e índice único para `user_id`.
2. Converter roles legadas e auditar valores inválidos antes de alterar o enum de `user`.
3. Publicar `GET`, `POST` e `PUT /user_profile` com autenticação e testes de propriedade.
4. Atualizar login, rotas de perfil e formulário; validar cliente e prestador em ambiente de teste.
5. Liberar a interface após verificar criação, leitura, atualização, logout e bloqueio de acesso cruzado.

Rollback: desativar as rotas de perfil e reverter o redirecionamento, mantendo o login anterior; remover endpoints/tabela `user_profile` somente após exportar os dados e confirmar que nenhum fluxo depende deles. A conversão de role deve ter uma migração reversa documentada (`cliente` -> `client`, `prestador` -> `provider`) caso seja necessário restaurar o contrato anterior.

## Open Questions

- O ambiente Xano de produção usará upload nativo de imagem ou uma URL externa controlada? O contrato mantém `foto_perfil` opcional para permitir definir isso sem mudar o fluxo textual.
