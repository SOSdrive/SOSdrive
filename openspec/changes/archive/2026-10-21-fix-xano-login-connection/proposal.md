## Why

O login existente não está completando o fluxo de autenticação de forma confiável quando o usuário envia suas credenciais, e a falha não deixa claro se o problema está na submissão, configuração ou comunicação com o Xano. A correção deve tornar o envio observável para o usuário, validar a chamada ao endpoint e manter as credenciais e o token protegidos no backend Reflex.

## What Changes

- Verificar e garantir a submissão do formulário de login por um único evento funcional, com botão desabilitado e indicação de carregamento enquanto a requisição estiver ativa.
- Validar a configuração de `XANO_API_URL` e enviar `POST <XANO_API_URL>/auth/login` com JSON contendo `email` e `password`.
- Exibir o erro de conexão solicitado para falhas de rede/configuração e a mensagem do Xano ou uma mensagem segura padrão para HTTP 400/401.
- Em autenticação bem-sucedida, manter token e identidade no estado server-side do Reflex e redirecionar para `/perfil-cliente` ou `/perfil-prestador` conforme o papel retornado.
- Distinguir indisponibilidade do endpoint de CORS: como a chamada HTTP é feita server-side, CORS do navegador não deve ser tratado como solução ou causa presumida.

## Capabilities

### New Capabilities

### Modified Capabilities
- `authentication/driver-login`: Atualizar o contrato de submissão, feedback de carregamento/erros e redirecionamento por papel, preservando a sessão segura server-side.

## Impact

- **Dentro do MVP:** sim; corrige o login existente de Motoristas e Prestadores.
- **Código potencialmente afetado:** cliente HTTP, estado/evento Reflex e formulário de login em `sosdrive.py`.
- **Configuração/API:** usar `XANO_API_URL` como base e o endpoint `POST /auth/login`; sem nova dependência nem alteração no endpoint Xano.
- **Dados e segurança:** nenhuma entidade do domínio é alterada. Senha não será persistida; token continuará exclusivamente no estado server-side do Reflex, conforme decisão confirmada pelo solicitante.
- **Reuso:** corrigir o cliente de autenticação e a tela já existentes, sem criar outro formulário ou fluxo paralelo.
- **Verificação:** testar contrato da requisição com mocks, configuração ausente, respostas 400/401, falha de rede e redirecionamento conforme o papel, além de validar a interação de carregamento no formulário.
