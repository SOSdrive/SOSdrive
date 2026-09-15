## Why

O CTA principal ainda leva diretamente ao login, mas o primeiro acesso deve começar pelo cadastro. Como o MVP atende dois públicos diferentes, a pessoa precisa escolher desde o início se está criando uma conta de cliente/motorista ou de prestador de serviço.

## What Changes

- Fazer `Conhecer a SOS Drive` abrir a tela de criação de conta.
- Adicionar seleção explícita entre `Cliente / Motorista` e `Prestador de serviço`.
- Adicionar cadastro visual com nome, email e senha.
- Manter os dados somente no estado local do Reflex nesta etapa.
- Exibir confirmação local de cadastro preparado, sem enviar dados ao Xano ou a qualquer banco.
- Manter um caminho `Já tenho uma conta` para a tela de login existente.
- Adiar a integração de persistência, endpoint e autenticação para uma change posterior.

## Capabilities

### New Capabilities

- `web/signup-role-selection`: Fluxo visual de cadastro com escolha entre cliente/motorista e prestador.

### Modified Capabilities

- Nenhuma. O comportamento de login existente permanece disponível e a mudança de navegação está coberta pela nova capability de cadastro.

## Impact

- **Frontend**: `sosdrive.py` receberá estado, eventos e componentes de cadastro no Reflex.
- **Banco e backend**: nenhum acesso, alteração de tabela ou alteração de endpoint nesta change.
- **Segurança**: senha não será persistida nem enviada; o formulário será apenas uma preparação visual local.
- **Domínio**: a seleção representa Motorista/Cliente ou Prestador, sem criar registros ainda.
