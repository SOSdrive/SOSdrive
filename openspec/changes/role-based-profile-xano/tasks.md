## 1. Modelo e migração Xano

- [x] 1.1 Atualizar `xano/table/user.xs` para aceitar somente as roles canônicas `cliente` e `prestador`, mapear registros legados e verificar que nenhum valor inválido permanece
- [x] 1.2 Criar `xano/table/user_profile.xs` com `id`, `user_id`, `nome_completo`, `cpf`, `telefone` e `foto_perfil`, índice único de `user_id` e verificar a referência para `user`
- [x] 1.3 Documentar e executar a migração reversível de `client`/`provider` para `cliente`/`prestador`, verificando contagens antes e depois da migração (7 registros migrados; contas sem classificação foram assumidas como `cliente`)

## 2. API e autorização backend

- [x] 2.1 Atualizar o endpoint Xano `POST /auth/login` e `GET /auth/me` para retornar a role canônica e verificar respostas para cliente, prestador e role inválida
- [x] 2.2 Criar `GET /user_profile` autenticado, derivando `user_id` de `$auth.id`, e verificar que retorna apenas o perfil do usuário autenticado
- [x] 2.3 Criar `POST /user_profile` autenticado para criação idempotente e `PUT /user_profile` para atualização, rejeitando `user_id` arbitrário e verificando tentativa de acesso cruzado
- [x] 2.4 Adicionar validação backend para CPF, telefone, foto opcional e unicidade do perfil, verificando respostas de validação e ausência de dados sensíveis nos logs

## 3. Integração Reflex e roteamento

- [x] 3.1 Reutilizar `AuthState` e o cliente Xano existente em `sosdrive.py` para carregar a role de `auth/me` antes do redirecionamento, verificando as rotas `/perfil-cliente` e `/perfil-prestador`
- [x] 3.2 Tratar role ausente ou inválida, sessão expirada e falhas de API com mensagens recuperáveis, limpar a senha após submit e verificar que token e senha não aparecem na UI
- [x] 3.3 Implementar um componente de formulário compartilhado para os dois perfis, reutilizando tokens de `styles.py` e verificando o layout responsivo em desktop e mobile
- [x] 3.4 Adicionar upload/URL opcional de foto, campos de nome completo, CPF e telefone com máscaras de exibição e valores normalizados enviados ao Xano; verificar edição, limpeza e carregamento de perfil vazio
- [x] 3.5 Conectar `Salvar/Atualizar Dados` aos endpoints de perfil, exibindo sucesso/erro sem duplicar registros, e verificar criação seguida de atualização

## 4. Verificação integrada

- [x] 4.1 Criar ou atualizar testes Python para role, normalização dos campos, erros de autenticação e payloads de perfil; verificar com `unittest` padrão do ambiente
- [x] 4.2 Validar sintaxe dos arquivos Xano e da aplicação Reflex, verificando `python -m py_compile sosdrive.py styles.py` e o validador Xano disponível
- [ ] 4.3 Executar `openspec validate role-based-profile-xano --type change --strict` e realizar teste manual completo de login cliente/prestador, leitura, atualização, logout e bloqueio de acesso cruzado (endpoint protegido validado com 401; teste autenticado ainda pendente)
