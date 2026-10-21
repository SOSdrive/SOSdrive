## 1. Inventory and restore

- [ ] 1.1 (reutilizar a estrutura OpenSpec existente) Inventariar os pacotes em
  `openspec/archive/` e identificar quais estão concluídos, incompletos ou
  conflitantes com nomes em `openspec/changes/`.
- [ ] 1.2 (reutilizar os artefatos existentes; sem editar o conteúdo) Mover
  somente os pacotes concluídos e sem colisões para `openspec/changes/`,
  preservando seus nomes e arquivos.
- [ ] 1.3 (operação de arquivos existente) Remover `openspec/archive/` somente
  se estiver vazia; preservar e reportar pacotes incompletos ou conflitantes.

## 2. Regra operacional

- [ ] 2.1 (documentação existente) Atualizar `AGENTS.md` para que mudanças
  concluídas permaneçam em `openspec/changes/` e não sejam movidas para
  `openspec/archive/` ao finalizar.

## 3. Verificação

- [ ] 3.1 (verificação da estrutura existente) Confirmar que os pacotes
  elegíveis foram restaurados sem perda ou alteração de conteúdo e que nenhum
  arquivo foi sobrescrito.
- [ ] 3.2 (validação OpenSpec) Executar a validação dos pacotes afetados se a
  CLI estiver disponível; se não houver pacotes arquivados, registrar que a
  migração não exigiu movimentações.
