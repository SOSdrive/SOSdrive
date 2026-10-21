## Por que

As mudanças do OpenSpec que já foram concluídas e arquivadas precisam continuar
disponíveis em `openspec/changes/`, junto às demais mudanças do projeto. No
estado atual do repositório não existe `openspec/archive/`, portanto não há
pacotes arquivados para restaurar agora; a proposta registra o procedimento
para restaurá-los caso estejam presentes no momento da aplicação.

## O que muda

- Restaurar para `openspec/changes/` cada pacote de mudança concluído encontrado
  em `openspec/archive/`.
- Registrar no fluxo operacional do projeto que mudanças concluídas devem
  permanecer em `openspec/changes/`, sem serem arquivadas ao finalizar.
- Preservar os arquivos e o conteúdo de cada pacote sem alterar seus artefatos.
- Remover a pasta `openspec/archive/` somente quando estiver vazia após a
  restauração.
- Interromper a restauração de qualquer pacote com conflito de nome ou conteúdo,
  sem sobrescrever nem descartar arquivos.
- Verificar e documentar o resultado; se não houver arquivo arquivado, concluir
  a verificação como nenhuma movimentação necessária.

## Capabilities

### Novas capabilities

- `openspec/change-archive-management`: restauração segura de mudanças
  concluídas do diretório de arquivo para o diretório ativo do OpenSpec.

### Capabilities modificadas

Nenhuma.

## Impacto

- **Escopo do MVP:** Não se aplica ao produto em execução; esta é uma tarefa de
  organização e manutenção dos artefatos de desenvolvimento.
- **Entidades do domínio:** nenhuma entidade de
  `docs/domain-model.md` é afetada.
- **Reuso:** utiliza a estrutura de diretórios e os artefatos OpenSpec existentes;
  não introduz código, dependências ou novas ferramentas.
- **Compatibilidade:** mantém o conteúdo e os nomes dos pacotes restaurados.
  Conflitos são reportados para resolução explícita em vez de sobrescrever
  mudanças ativas.
- **Rollback:** se necessário, os diretórios restaurados podem ser movidos de
  volta ao arquivo após verificar que a restauração não alterou seu conteúdo.
