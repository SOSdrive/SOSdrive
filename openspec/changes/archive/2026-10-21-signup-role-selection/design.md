## Context

A aplicação Reflex atualmente usa `AppState.screen` para alternar entre apresentação, login e autenticado. O CTA `Conhecer a SOS Drive` chama `open_login`. Nesta etapa, o produto quer validar a experiência de cadastro e escolha de público antes de conectar persistência.

## Decisions

- Adicionar o estado `signup` como tela inicial do CTA e manter `login` como caminho secundário.
- Adicionar `signup_role` com valores locais `client` e `provider`; o valor inicial será `client`.
- Adicionar campos locais de nome, email e senha.
- O submit fará somente validação local e mostrará confirmação visual; não chamará `requests`, Xano ou banco.
- Limpar a senha após submit, erro ou retorno de tela.
- Não alterar `xano/`, tabelas, endpoints, funções ou contratos de autenticação nesta change.
- Reutilizar os tokens e componentes visuais existentes do Reflex.

## State transitions

- `presentation` -> `signup`: CTA principal.
- `signup` -> `login`: ação `Já tenho uma conta`.
- `signup` -> `presentation`: ação de retorno.
- `signup` -> confirmação local: submit válido.
- `signup` permanece na mesma tela: submit incompleto.

## Verification

- `openspec validate signup-role-selection --type change --strict`.
- `python -m py_compile sosdrive.py styles.py rxconfig.py`.
- Build/export Reflex.
- Teste local dos handlers de seleção e validação sem mock de rede, confirmando que nenhuma chamada HTTP é feita.
