## Why

A tela de login atualmente não aproveita o espaço de fundo para reforçar a identidade visual e manter o interesse do usuário. Um vídeo de fundo em tela cheia, escurecido por uma sobreposição, dará contexto visual à SOS Drive sem prejudicar a leitura ou o uso do formulário.

## What Changes

- Adicionar vídeo de fundo à tela de login, com reprodução automática, repetição contínua, sem áudio e compatível com reprodução inline em dispositivos móveis.
- Manter o vídeo em uma URL facilmente substituível, usando o vídeo local já disponível em `assets/` como fonte inicial.
- Aplicar cobertura proporcional da área de fundo e uma camada escura entre o vídeo e o conteúdo.
- Preservar o cartão de login opaco, responsivo e alinhado à esquerda, além dos campos, ações e fluxo de autenticação existentes.

## Capabilities

### New Capabilities
- `web/login-background-video`: Requisitos visuais e de interação do vídeo de fundo na tela de login.

### Modified Capabilities

## Impact

- **Dentro do MVP:** sim; é uma melhoria visual da tela de autenticação existente.
- **Código potencialmente afetado:** componente `login_screen` em `sosdrive.py` e estilos globais em `styles.py`.
- **Ativo:** reutilizar o vídeo já presente em `assets/`; manter sua localização configurável para permitir substituição sem reestruturar a tela.
- **Comportamento preservado:** autenticação, navegação, validação, feedback e dados existentes não mudam.
- **Domínio:** nenhuma entidade (Motorista, Prestador, Tipo de Socorro, Chamado, Avaliação ou Localização) é criada, lida, atualizada ou removida por esta alteração.
- **Dependências e APIs:** sem novas dependências ou mudanças de API.
- **Verificação:** validar os atributos e camadas do vídeo, a legibilidade e interação do cartão, a responsividade em desktop e mobile, e o fallback visual caso o vídeo não carregue ou o navegador não permita autoplay.
