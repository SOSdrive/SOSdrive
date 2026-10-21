## Why

A arquitetura anterior dependia de outro framework Python, mas a decisão do projeto mudou para Reflex, mantendo Python no frontend e no backend. A migração precisa preservar a landing pública, o fluxo de login Xano e a execução local, removendo a dependência e os comandos específicos do framework anterior.

## What Changes

- **BREAKING**: usar Reflex como framework da aplicação web.
- Converter a landing pública e o fluxo de login Xano para componentes e estado Reflex.
- Preservar o CTA `Conhecer a SOS Drive`, o formulário de email/senha e os estados de autenticação.
- Reorganizar o entrypoint para o padrão de aplicação Reflex e atualizar o comando local.
- Substituir dependências, setup e referências documentais do framework anterior por Reflex.
- Adaptar o módulo de estilos para CSS global/estilos Reflex, preservando responsividade, acessibilidade e movimento reduzido.
- Manter a integração Xano, sem mover regras de autorização para o frontend.

## Capabilities

### New Capabilities

- `web/reflex-application`: Aplicação web SOS Drive executável com Reflex, incluindo landing pública e roteamento de tela.

### Modified Capabilities

- `authentication/driver-login`: Preservar o login do motorista com Xano durante a migração do frontend para Reflex.

## Impact

- **Código**: `presentation_screen.py`, `styles.py` e possível novo entrypoint `sosdrive.py`.
- **Dependências**: adicionar Reflex e manter `requests` para Xano.
- **Execução**: atualizar `setup.ps1`, `README.md` e instruções para `reflex run`.
- **Documentação**: atualizar `AGENTS.md`, `docs/project-overview.md` e `openspec/config.yaml` para refletir Reflex.
- **Backend Xano**: sem alteração de endpoints ou regras de autorização.
- **Domínio**: nenhuma alteração em Motorista, Prestador, Chamado, Tipo de Socorro, Avaliação ou Localização.
