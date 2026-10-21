## Por que

A tela `/home_provider` precisa permitir que o Prestador controle com clareza
se está disponível para chamados e recupere o mapa para sua posição atual.
Atualmente há um checkbox de disponibilidade pouco destacado, o mapa inicia em
uma coordenada fixa e o comando genérico de centralização não encontra um
marcador da posição do Prestador nessa tela.

## O que muda

- Tornar o estado disponível/indisponível visível e fácil de alternar no
  cabeçalho da Home do Prestador, com texto e indicação visual consistentes.
- Fazer o mapa da Home do Prestador iniciar na localização atual do Prestador
  quando a geolocalização do navegador estiver disponível.
- Adicionar ação explícita para centralizar novamente o mapa na posição atual,
  inclusive depois de o usuário mover ou afastar o mapa.
- Tratar permissão negada ou geolocalização indisponível com feedback acessível
  e manter o mapa navegável em uma posição padrão, sem travar a tela.
- Manter a regra existente: solicitações próximas são exibidas quando o
  Prestador está disponível e ocultadas quando está indisponível.

## Capabilities

### Novas capabilities

Nenhuma.

### Capabilities modificadas

- `provider-home`: melhorar o controle de disponibilidade e a centralização do
  mapa na posição atual do Prestador.

## Impacto

- **Dentro do MVP:** Sim; aprimora a operação já prevista da Home do Prestador.
- **Entidades:** atualiza o estado de disponibilidade do Prestador e usa sua
  Localização atual; não altera Chamado, Tipo de Socorro ou Avaliação.
- **Reuso:** reutiliza `OperationalState.is_available`, o mapa Leaflet existente,
  a infraestrutura de geolocalização do navegador e os componentes/styles
  existentes em Reflex.
- **API/dados:** sem novos endpoints, alterações de banco ou mudança de
  autorização. O estado permanece no fluxo local/mock atual desta Home.
- **Verificação:** testar alternância online/offline, inicialização do mapa,
  recentralização após pan/zoom e falha de permissão de localização.
- **Rollback:** reverter a apresentação do controle e a ação de centralização;
  não há migração de dados.
