# Project Overview — SOS Drive

## 1. Visão geral

SOS Drive é uma plataforma que conecta motoristas a prestadores de serviço de socorro veicular, permitindo localizar ajuda próxima, solicitar atendimento e acompanhar o chamado em tempo real.

## 2. Problema

Atualmente, muitos motoristas enfrentam dificuldades quando o veículo apresenta problemas inesperados, como pane mecânica, pneu furado, bateria descarregada ou falta de combustível. Em situações como essas, encontrar rapidamente um serviço de socorro confiável e próximo pode ser difícil, principalmente em locais desconhecidos ou durante a noite.

Além disso, o motorista muitas vezes não sabe qual profissional está disponível, quanto tempo levará para chegar ou qual será o custo aproximado do atendimento.

## 3. Objetivos

Facilitar a comunicação entre motoristas e prestadores de serviços de socorro veicular, permitindo:

- localizar ajuda próxima;
- solicitar atendimento de forma rápida;
- acompanhar a situação do chamado do início ao fim.

## 4. Público-alvo / usuários

- **Motoristas**: pessoas que precisam de socorro veicular em situações de pane, pneu furado, bateria descarregada ou falta de combustível.
- **Prestadores de serviço**: profissionais ou empresas que oferecem atendimento de socorro veicular.

## 5. Escopo

O escopo inicial (MVP) cobre o fluxo essencial de solicitar e receber socorro veicular. Funcionalidades adicionais (pagamentos, histórico avançado, integrações externas, etc.) ficam fora do MVP e devem ser tratadas como evoluções futuras.

## 6. Principais funcionalidades

MVP:

- Cadastro de usuários e prestadores.
- Cadastro dos tipos de socorro (pane mecânica, pneu furado, bateria descarregada, falta de combustível).
- Solicitação de atendimento.
- Localização (do motorista e do prestador).
- Acompanhamento do chamado.
- Avaliação do atendimento.

## 7. Requisitos e restrições importantes

- O motorista precisa conseguir identificar prestadores disponíveis próximos.
- O motorista precisa ter visibilidade do status do chamado (solicitado, a caminho, em atendimento, concluído).
- O sistema deve suportar cenários de uso a qualquer hora do dia, incluindo à noite.

## 8. Arquitetura tecnológica

- Backend/lógica em **Python**.
- Frontend em **Streamlit**.
- Desenvolvimento conduzido com **OpenSpec** (proposta de spec antes da implementação).

## 9. Princípios de desenvolvimento

- Seguir o fluxo OpenSpec para mudanças funcionais.
- Priorizar simplicidade no MVP; evitar complexidade prematura.
- Manter consistência visual e de UX entre as telas (ver diretrizes de UI do projeto).

## 10. Segurança e integridade

- Regras de autorização aplicadas no backend.
- Dados de localização e cadastro tratados com cuidado quanto à privacidade dos usuários e prestadores.

## 11. Estratégia de desenvolvimento

- Início pela primeira tela (landing page), seguindo processo estruturado de UX/UI (persona, user flow, arquitetura de informação, diretrizes de UI, acessibilidade).
- Evolução incremental das demais funcionalidades do MVP.

## 12. Fonte de verdade e documentação

Este documento descreve a visão geral do projeto e deve permanecer relativamente estável. Detalhes de implementação, endpoints, modelo de dados e comportamento tela a tela pertencem às specs do OpenSpec e à documentação de UX/UI — não a este arquivo.