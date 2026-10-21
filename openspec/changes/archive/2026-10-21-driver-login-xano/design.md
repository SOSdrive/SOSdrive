## Context

`sosdrive.py` é uma landing pública Reflex. O CTA principal abre o login. O backend Xano já possui `POST auth/login`, que recebe `email` e `password` e retorna `authToken` e `user_id`.

A URL pública do workspace Xano não está versionada no projeto. A integração precisa ser configurável sem expor endpoint sensível, credenciais ou senha do usuário no código.


## Decisions

### Navigation and state

Usar estado server-side Reflex com os estados `presentation`, `login` e `authenticated`. O clique do CTA define `screen = "login"`; o botão de retorno define `screen = "presentation"`. Após autenticação, a tela permanece no contexto autenticado e mostra o identificador do usuário sem exibir o token.

### Xano client boundary

Adicionar funções pequenas em `presentation_screen.py` para:

- obter a URL pela variável de ambiente `XANO_API_URL`;
- normalizar a URL e anexar `/auth/login`;
- executar `requests.post(..., json={"email": ..., "password": ...}, timeout=10)`;
- interpretar somente `authToken` e `user_id` da resposta.

A senha será usada apenas durante a requisição e não será colocada no estado Reflex, logs ou mensagens. O backend Xano continua responsável por validar a senha e emitir o token.

### Error handling

Distinguir configuração ausente, credenciais rejeitadas e indisponibilidade/erro inesperado. Mensagens exibidas ao usuário serão genéricas e não incluirão corpo bruto da resposta, token ou senha.

### Configuration

A configuração local usará:

```toml
XANO_API_URL="https://<workspace>.n7.xano.io/api:<group>"
```

Como alternativa, `XANO_API_URL` pode ser definida no ambiente do processo. O endpoint final esperado é `<XANO_API_URL>/auth/login`.

## Affected entities

- **Motorista**: autenticado; nenhum atributo de domínio é alterado.
- **Chamado, Prestador, Tipo de Socorro, Avaliação, Localização**: não são alterados nesta change.

## Verification

- `python -m py_compile presentation_screen.py styles.py`
- Teste com URL ausente para confirmar que nenhuma chamada é feita.
- Teste manual no Reflex com resposta Xano de sucesso e erro de credenciais.
- `openspec validate driver-login-xano --type change --strict`
