# AGENTS.md — SOS Drive

Este arquivo define regras operacionais relativamente estáveis para qualquer agente (humano ou IA) que for realizar alterações neste projeto. Ele não substitui a documentação do projeto (specs, OpenSpec, docs de UX) — apenas orienta como agir sobre ela.

## Documentação

```text
Antes de realizar alterações significativas,
consultar os documentos de contexto do projeto
(specs em OpenSpec, docs de UX/UI, decisões já registradas).
```

## Arquitetura

```text
Respeitar as tecnologias definidas no projeto:
Python no backend/lógica e Streamlit no frontend.
Não introduzir tecnologias alternativas
(outro framework de frontend, outra linguagem, etc.)
sem justificativa explícita e registrada.
```

## Código

```text
Reutilizar código existente quando apropriado.
Evitar duplicação.
Não modificar funcionalidades não relacionadas
à mudança atual sem justificativa.
```

## Segurança

```text
Regras de autorização devem ser aplicadas no backend,
nunca apenas no frontend/Streamlit.
```

## Desenvolvimento

```text
Mudanças devem utilizar OpenSpec
(proposta de spec antes da implementação,
conforme fluxo já adotado no projeto).
```

## Testes

```text
Mudanças funcionais devem possuir estratégia de verificação
(manual ou automatizada) antes de serem consideradas concluídas.
```

---

## O que não colocar neste arquivo

Não transformar o AGENTS.md em uma cópia de toda a documentação do projeto.

Evitar repetir aqui:
- todos os requisitos;
- todas as entidades;
- todas as funcionalidades;
- todos os detalhes da arquitetura.

O agente deve consultar os demais documentos (specs OpenSpec, docs de UX) para esses detalhes.

O AGENTS.md deve funcionar como um **conjunto de regras operacionais**, não como fonte única de verdade sobre o produto.