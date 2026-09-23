## Why

O login atual autentica o usuário, mas ainda não transforma a role retornada pelo Xano em uma experiência direcionada nem oferece uma área para manter os dados cadastrais. O próximo passo do MVP é separar a jornada de prestadores e clientes e permitir que ambos mantenham um perfil vinculado à conta autenticada.

## What Changes

- Garantir que `user.role` aceite exclusivamente `prestador` ou `cliente` e que o login retorne essa informação junto do token.
- Redirecionar usuários autenticados para `/perfil-prestador` ou `/perfil-cliente` conforme a role validada no backend.
- Criar uma página de perfil com upload/URL de foto, nome completo, CPF, telefone e ação laranja de salvar/atualizar.
- Criar a tabela relacional `user_profile`, vinculada a `user` por `user_id`, e seus endpoints autenticados de leitura e gravação.
- Aplicar o padrão visual existente: fundo off-white, títulos azul-marinho, ações laranja, estados de foco azul-marinho e alertas vermelhos.
- Não alterar o ciclo de vida de Chamado, Avaliação, Localização ou os fluxos de atendimento.

## Capabilities

### New Capabilities

- `authentication/role-based-profile`: Login direcionado por role e manutenção do perfil cadastral autenticado.

### Modified Capabilities

- `authentication/driver-login`: O contrato de login passa a retornar e validar a role do usuário antes do redirecionamento.

## Impact

- **Frontend**: `sosdrive.py` ganhará o roteamento por role, as rotas de perfil e o formulário responsivo consistente com o design atual.
- **Backend Xano**: a tabela `user` terá a role normalizada; será criada `user_profile` com referência para `user`; serão expostos `GET` e `POST/PUT /user_profile` protegidos por token.
- **Autorização**: o backend deverá derivar o `user_id` do token e impedir leitura ou alteração do perfil de outra conta; a role também será validada no servidor.
- **Domínio**: amplia os dados cadastrais de Motorista e Prestador sem modificar Chamado, Tipo de Socorro, Avaliação ou Localização.
- **Dependências**: reutiliza Python, Reflex, `requests` e os endpoints de autenticação Xano existentes; não introduz tecnologia de frontend alternativa.
- **MVP**: permanece dentro do escopo de cadastro e autenticação. A migração pode ser revertida removendo a tabela `user_profile`, os endpoints associados e o roteamento de perfil, preservando os dados da tabela `user`.
