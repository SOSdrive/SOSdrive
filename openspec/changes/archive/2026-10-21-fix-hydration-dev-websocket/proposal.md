## Why

The Reflex app currently injects `rx.html` fragments through `head_components`, which can render wrapper `<div>` elements inside `<head>` and trigger React hydration failures. Development logs also show frontend runtime requests targeting a different port than the app's configured frontend, making HMR/WebSocket connectivity unreliable.

## What Changes

- Replace invalid HTML-fragment injection in document head components with Reflex-supported, semantically valid stylesheet and script loading.
- Initialize map helpers only after their required browser libraries are available, without changing the map experience.
- Align development frontend and backend WebSocket/HMR URLs with the active app host and configured ports, and document safe local startup/verification.
- Keep browser-only state out of server-rendered initial markup and preserve existing login and route behavior.

## Capabilities

### New Capabilities
- `web/runtime-stability`: Valid server-rendered HTML, hydration-safe browser initialization, and reliable development HMR/WebSocket connections for the Reflex app.

### Modified Capabilities

## Impact

- **Dentro do MVP:** sim; esta mudança estabiliza a execução e o desenvolvimento do app existente.
- **Código potencialmente afetado:** configuração `rx.App` e carregamento de recursos em `sosdrive.py`, configuração Reflex em `rxconfig.py` e documentação local de desenvolvimento, se necessária.
- **Reutilização:** corrige a composição Reflex e a configuração de ambiente já existentes; não adiciona framework nem dependência.
- **Domínio:** nenhuma entidade (Motorista, Prestador, Tipo de Socorro, Chamado, Avaliação ou Localização) é alterada.
- **APIs e dados:** sem alteração de endpoints ou dados persistidos.
- **Verificação:** compilar o app, confirmar HTML de head válido e testar carregamento do app e conexão HMR/WebSocket nas portas de desenvolvimento configuradas.
