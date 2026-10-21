## Why

O CTA principal da apresentação atualmente apenas exibe uma confirmação e não conduz o motorista para a operação. O login via Xano é necessário agora para proteger o acesso às próximas etapas do MVP e permitir que o motorista seja identificado antes de solicitar ou acompanhar um chamado.

## What Changes

- Fazer o botão `Conhecer a SOS Drive` abrir uma tela de login dentro da aplicação Reflex.
- Adicionar campos obrigatórios de email e senha.
- Integrar o formulário ao endpoint Xano `POST auth/login` usando uma URL configurável por `XANO_API_URL`.
- Armazenar o token de autenticação somente no estado server-side do Reflex após sucesso.
- Exibir mensagens claras para credenciais inválidas, falha de conexão e configuração ausente.
- Permitir retorno da tela de login para a apresentação sem autenticar.
- Não implementar cadastro, recuperação de senha ou fluxo operacional nesta change.

## Capabilities

### New Capabilities

- `authentication/driver-login`: Login de motorista com email e senha por meio do endpoint de autenticação Xano.

### Modified Capabilities

- Nenhuma.

## Impact

- **Frontend**: `presentation_screen.py` receberá uma tela de login e o novo comportamento do CTA.
- **Integração**: chamada HTTP para o endpoint Xano `auth/login`; a base da API será lida de `XANO_API_URL`.
- **Sessão**: o token e o identificador do usuário serão mantidos no estado server-side do Reflex somente durante a sessão ativa.
- **Segurança**: senha não será persistida nem registrada; a autorização continuará sendo validada pelo backend Xano.
- **Dependências**: será reutilizado o cliente HTTP já disponível via `requests`, sem nova tecnologia de frontend.
- **Domínio**: autentica o Motorista; não altera Chamado, Prestador, Tipo de Socorro, Avaliação ou Localização.
