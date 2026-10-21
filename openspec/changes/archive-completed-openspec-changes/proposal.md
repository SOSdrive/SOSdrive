## Por que

Mudanças concluídas não devem permanecer indefinidamente entre as mudanças
ativas do OpenSpec. Elas precisam ser retiradas de `openspec/changes/` pelo
arquivo nativo do OpenSpec quando disponível, preservando seus artefatos e
mantendo o diretório ativo focado no trabalho em andamento.

Esta proposta define o comportamento oposto ao da mudança existente
`restore-archived-openspec-changes`, que propõe restaurar mudanças arquivadas
para a área ativa. O nome distinto evita confundir os dois fluxos; esta
proposta não altera nem substitui aquela mudança.

## O que muda

- Definir critérios para considerar uma mudança elegível ao arquivamento:
  todas as tarefas marcadas como concluídas; em mudanças sem `tasks.md`,
  exigir evidência explícita de conclusão nos demais artefatos.
- Preferir o comando e o formato nativos do OpenSpec. Se o CLI não estiver
  disponível, permitir a movimentação conservadora do pacote completo para o
  formato de arquivo OpenSpec, sem alterar seu conteúdo, somente depois de
  conferir a elegibilidade e a ausência de colisões.
- Tratar colisões de destino e inconsistências como bloqueios seguros:
  interromper o pacote afetado, sem sobrescrever, renomear ou descartar
  conteúdo.
- Verificar estrutura e conteúdo antes/depois, manter mudanças incompletas na
  área ativa e registrar quando a validação nativa não puder ser executada.

## Capabilities

### Novas capabilities

- `openspec/change-archive-management`: arquivamento seguro e verificável de
  mudanças OpenSpec concluídas.

### Capabilities modificadas

Nenhuma.

## Impacto

- **Escopo do MVP:** Não se aplica ao produto em execução; é uma prática de
  manutenção dos artefatos de desenvolvimento.
- **Entidades do domínio:** nenhuma entidade de `docs/domain-model.md` é
  afetada.
- **Reuso:** utiliza o CLI e o formato de arquivo nativos do OpenSpec quando
  disponíveis e os artefatos existentes; o fallback preserva o pacote no
  formato de arquivo OpenSpec e não introduz código ou dependências.
- **Compatibilidade:** mudanças não concluídas continuam na área ativa.
  Colisões ou falhas de validação não autorizam sobrescrita ou remoção.
- **Relação com outra mudança:** não modifica os arquivos de
  `restore-archived-openspec-changes`, nem aplica a restauração descrita por
  ela.
- **Rollback:** se o arquivamento produzir um resultado incorreto, preservar o
  conteúdo existente e seguir o fluxo nativo e explícito de restauração do
  OpenSpec após inspecionar o destino. Não mover diretórios manualmente nem
  sobrescrever pacotes para tentar reverter automaticamente.
