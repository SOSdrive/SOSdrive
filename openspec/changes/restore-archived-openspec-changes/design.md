## Contexto

O OpenSpec deste repositório usa `openspec/changes/` para pacotes de mudança.
Uma inspeção em 2026-10-17 não encontrou o diretório `openspec/archive/`; logo,
nenhum pacote arquivado está disponível para ser movido atualmente.

## Objetivos e não objetivos

### Objetivos

- Manter pacotes de mudanças concluídas e arquivadas no diretório
  `openspec/changes/`.
- Preservar integralmente os artefatos de cada pacote durante a movimentação.
- Tornar conflitos e pacotes não concluídos explícitos, sem perda de dados.

### Não objetivos

- Alterar artefatos de especificação, tarefas ou código da aplicação durante a
  restauração.
- Mover mudanças ativas que já estejam em `openspec/changes/`.
- Alterar o CLI ou a automação interna do OpenSpec para impedir tecnicamente
  operações de arquivamento.
- Apagar pacotes incompletos ou resolver automaticamente colisões de nomes.

## Decisões

1. Fazer primeiro um inventário dos diretórios de mudança sob
   `openspec/archive/`. Considerar restauráveis os pacotes que estejam
   concluídos; quando houver `tasks.md`, confirmar que todas as tarefas estão
   marcadas como concluídas.
2. Mover cada pacote restaurável para `openspec/changes/<nome>`, mantendo toda a
   estrutura interna. Não editar o conteúdo dos artefatos durante a migração.
3. Se o nome já existir em `openspec/changes/`, comparar os conteúdos e não
   sobrescrever. Interromper esse pacote e reportar o conflito para resolução
   manual; continuar apenas com os outros pacotes sem conflito.
4. Não mover pacotes que não possam ser confirmados como concluídos. Reportar
   sua localização e motivo, preservando-os sem alterações.
5. Remover `openspec/archive/` somente se estiver vazia após a movimentação.
   Caso não exista ou não haja pacote elegível, registrar que nenhuma
   movimentação foi necessária.
6. Registrar em `AGENTS.md` que mudanças concluídas devem permanecer em
   `openspec/changes/` e não devem ser arquivadas como parte da conclusão.
   Esta é uma regra operacional para o fluxo do projeto, não uma alteração do
   comportamento do CLI OpenSpec.
7. Verificar o resultado pela lista de diretórios e pela comparação dos
   conteúdos antes/depois; validar os artefatos com a CLI OpenSpec se ela
   estiver disponível.

## Riscos e compensações

- **Colisão com uma mudança ativa:** não sobrescrever; parar e reportar a
  colisão para resolução explícita.
- **Pacote incompleto dentro do arquivo:** manter no lugar e reportar, em vez de
  apresentá-lo como concluído.
- **Ausência do diretório de arquivo:** tratar como operação sem movimentações,
  não criar uma pasta vazia sem necessidade.
- **CLI OpenSpec indisponível:** validar a estrutura e integridade dos arquivos
  localmente e informar a limitação.

## Plano de migração

1. Inventariar `openspec/archive/`, se existir, e registrar os pacotes elegíveis,
   incompletos e conflitantes.
2. Restaurar os pacotes concluídos e sem colisões para `openspec/changes/`.
3. Remover o diretório de arquivo apenas se ficar vazio.
4. Confirmar que cada pacote restaurado mantém seus arquivos e conteúdo.

Nenhum dado de produto é alterado. O rollback consiste em mover os pacotes
restaurados de volta para `openspec/archive/` após confirmar que não foram
editados desde a restauração.

## Verificação

- Confirmar a lista de pacotes arquivados antes e depois da operação.
- Verificar que cada pacote elegível aparece em `openspec/changes/` com o mesmo
  conteúdo e que nenhum pacote foi sobrescrito.
- Confirmar que pacotes incompletos ou conflitantes foram preservados e
  reportados.
- Confirmar que `openspec/archive/` foi removido somente quando ficou vazio.
- Executar a validação OpenSpec quando a CLI estiver disponível.
