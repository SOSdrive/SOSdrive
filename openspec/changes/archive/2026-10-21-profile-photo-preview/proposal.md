## Why

A seleção de uma foto no perfil não está resultando em uma pré-visualização confiável no avatar, deixando o usuário sem confirmação visual antes de salvar. A correção deve tornar a seleção imediatamente visível e preservar a imagem escolhida para o fluxo de gravação já existente.

## What Changes

- Garantir que a seleção de uma imagem válida atualize imediatamente o avatar do perfil.
- Priorizar a imagem recém-selecionada sobre a foto persistida e, na ausência de ambas, manter as iniciais como fallback.
- Reutilizar o estado e o fluxo Reflex de upload/gravação existentes; não enviar a imagem ao Xano antes de o usuário salvar.
- Preservar a apresentação circular da imagem sem distorção, tanto para a prévia quanto para a foto persistida.

## Capabilities

### New Capabilities
- `profile/photo-preview`: Comportamento visível de seleção e pré-visualização local da foto do perfil antes de salvar.

### Modified Capabilities

## Impact

- **Dentro do MVP:** sim; melhora a edição do perfil existente.
- **Código afetado:** estado `AppState`, manipulador Reflex de upload, avatar e formulário de perfil em `sosdrive.py`; estilos relacionados em `styles.py`, se necessário.
- **Reutilização:** aproveita o estado `selected_profile_image`, `user_profile_photo` e o fluxo de salvamento de perfil já existentes; não adiciona framework ou dependência.
- **APIs e dados:** sem novo endpoint ou alteração do modelo de domínio; o envio ao Xano continua condicionado à ação de salvar.
- **Entidades:** afeta apenas a apresentação dos dados de perfil de Motorista e Prestador; Chamado, Tipo de Socorro, Avaliação e Localização não mudam.
- **Verificação:** exercitar seleção válida, prioridade sobre foto persistida, fallback para iniciais e preservação do envio no salvamento, sem persistência antes dessa ação.
