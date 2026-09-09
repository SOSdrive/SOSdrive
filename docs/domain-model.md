# Domain Model — SOS Drive

Este documento descreve os conceitos fundamentais do domínio do SOS Drive e como eles se relacionam. Representa conceitos do negócio, não necessariamente tabelas do banco de dados.

```text
Usuário (Motorista)
   │
   └── Chamado
           │
           ├── Tipo de Socorro
           ├── Prestador
           ├── Localização
           └── Avaliação

Prestador
   │
   └── Chamado
```

## Motorista

Representa o usuário que solicita socorro veicular.

### Principais informações

- nome;
- contato;
- veículo (opcional/dados básicos);
- histórico de chamados.

### Responsabilidade

Criar um chamado informando o tipo de socorro necessário e sua localização, acompanhar o andamento do atendimento e avaliar o serviço prestado ao final.

### Relacionamentos

Um motorista pode abrir vários chamados.

Um chamado pertence a um único motorista.

## Prestador

Representa o profissional ou empresa que presta o serviço de socorro veicular.

### Principais informações

- nome/razão social;
- contato;
- tipos de socorro que atende;
- localização/área de atuação;
- disponibilidade (disponível/indisponível).

### Responsabilidade

Receber e aceitar chamados, atender às solicitações e atualizar o status do atendimento.

### Relacionamentos

Um prestador pode atender vários chamados (ao longo do tempo, não simultaneamente).

Um chamado é atendido por, no máximo, um prestador por vez.

## Tipo de Socorro

Representa a categoria do problema enfrentado pelo motorista.

### Principais informações

- nome (ex.: pane mecânica, pneu furado, bateria descarregada, falta de combustível);
- descrição.

### Responsabilidade

Classificar o chamado, permitindo que prestadores compatíveis sejam identificados.

### Relacionamentos

Um tipo de socorro pode estar associado a vários chamados.

Um chamado possui um único tipo de socorro.

## Chamado

Representa uma solicitação de atendimento feita por um motorista.

### Principais informações

- tipo de socorro;
- localização do motorista;
- status (solicitado, a caminho, em atendimento, concluído, cancelado);
- horário de solicitação;
- horário de conclusão.

### Responsabilidade

Concentrar as informações da solicitação e seu ciclo de vida, do momento em que é criado até sua conclusão.

### Relacionamentos

Um chamado pertence a um motorista.

Um chamado pode ser atendido por um prestador.

Um chamado possui um tipo de socorro.

Um chamado pode gerar uma avaliação.

### Regras estruturais importantes

Um chamado só pode ser avaliado após ser concluído.

Um chamado só pode estar associado a um prestador por vez.

## Avaliação

Representa a opinião do motorista sobre o atendimento recebido.

### Principais informações

- nota;
- comentário (opcional).

### Responsabilidade

Registrar a percepção do motorista sobre a qualidade do atendimento prestado.

### Relacionamentos

Uma avaliação pertence a um único chamado.

Um chamado possui, no máximo, uma avaliação.

## Localização

Representa a posição geográfica utilizada para aproximar motorista e prestador.

### Principais informações

- coordenadas (latitude/longitude) ou endereço.

### Responsabilidade

Permitir localizar prestadores próximos e acompanhar o deslocamento até o motorista.

### Relacionamentos

Um chamado possui uma localização de origem (motorista).

Um prestador possui uma localização atual/área de atuação.