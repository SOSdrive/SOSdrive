## Contexto

A Home do Prestador (`/home_provider`) é implementada em Reflex e usa Leaflet
por meio do wrapper JavaScript existente em `window.initSOSMap`. A tela inicia
o mapa no centro fixo de São Paulo. Existe um checkbox ligado a
`OperationalState.is_available`, mas o mapa dessa Home não cria nem atualiza um
marcador da posição do Prestador; por isso, o controle genérico
`window.centerMap` não garante que a ação recoloque o mapa na posição correta.

## Objetivos e não objetivos

### Objetivos

- Tornar o estado online/indisponível perceptível e simples de alterar na Home
  do Prestador.
- Usar geolocalização do navegador para obter e representar a posição atual do
  Prestador no mapa.
- Permitir recentralização a qualquer momento, independentemente do pan/zoom
  atual do mapa.
- Comunicar falha de permissão/geolocalização e manter uma posição padrão como
  fallback.
- Preservar a exibição de solicitações conforme o estado de disponibilidade.

### Não objetivos

- Persistir disponibilidade ou localização no Xano ou criar endpoints.
- Alterar o fluxo de aceite, recusa ou atendimento de Chamados.
- Iniciar rastreamento contínuo em background ou solicitar permissão sem ação
  explícita do usuário, além do comportamento necessário para inicializar o
  mapa.
- Alterar telas de Motorista ou o mapa de atendimento em andamento.

## Decisões

1. Reutilizar `OperationalState.is_available` e `toggle_provider_status`.
   Apresentar controle acionável com rótulo de estado ("Disponível" /
   "Indisponível") e affordance visual compreensível; preservar o estado e as
   regras de lista existentes.
2. Acrescentar uma função JavaScript focada no mapa `provider-home-map` para
   obter a geolocalização do navegador, criar/atualizar o marcador do Prestador
   e usar `map.setView` para recentralizar. A posição é obtida quando a tela
   monta e novamente quando o Prestador aciona "Centralizar no meu local".
3. Manter o mapa padrão atual enquanto a posição não está disponível. Quando a
   geolocalização for negada ou falhar, mostrar uma mensagem breve e segura e
   permitir tentativa posterior pelo mesmo controle. Não impedir toggle,
   solicitações ou navegação do mapa.
4. Usar o mapa e o tema visual existentes, garantindo que controles sejam
   visíveis em telas estreitas e não cubram o cabeçalho nem a lista de
   solicitações.
5. Não alterar chamadas Xano, persistência de disponibilidade, autorização ou
   estado de Localização fora do escopo da Home do Prestador.

## Riscos e compensações

- **Permissão de localização negada:** manter o mapa na posição padrão e
  fornecer feedback e nova tentativa acionável.
- **Mapa já afastado pelo usuário:** o controle explícito solicita a posição
  atual novamente, sem depender de um marcador criado por outra tela.
- **Tela pequena ou controles sobrepostos:** verificar layout responsivo e
  posicionamento dos botões em viewport móvel e desktop.
- **Estado mock não persistido:** documentar que a alternância continua local,
  compatível com o fluxo atual, sem indicar sincronização com Xano.

## Plano de migração

Sem migração de dados ou mudanças externas. A alteração usa o estado local e
integração de mapa já existentes. Rollback consiste em restaurar o cabeçalho e
as funções de mapa anteriores.

## Verificação

- Verificar que o Prestador pode alternar disponibilidade e que rótulo, ícone,
  cor e lista de solicitações acompanham o estado.
- Simular geolocalização disponível e confirmar marcador e centro inicial no
  local retornado pelo navegador.
- Mover/afastar o mapa e acionar centralização; confirmar retorno à posição
  atual sem recriar a página.
- Simular permissão negada/erro e confirmar feedback, fallback e possibilidade
  de tentar novamente.
- Testar viewport móvel e desktop; executar testes Python relevantes e validar
  a compilação Reflex.
