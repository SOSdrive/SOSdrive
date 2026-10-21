## Contexto

O repositório usa o schema `spec-driven` do OpenSpec. Os pacotes ativos ficam
em `openspec/changes/` e incluem proposta, tarefas, design e, quando aplicável,
delta de especificação. Uma mudança concluída ainda nessa área mistura
referências históricas com trabalho ativo.

O repositório também contém uma mudança separada chamada
`restore-archived-openspec-changes`, que descreve o sentido inverso. Este
design registra somente a política de arquivar mudanças concluídas por meio
do mecanismo nativo do OpenSpec. Não altera, executa nem tenta reconciliar a
outra mudança.

## Objetivos e não objetivos

### Objetivos

- Retirar da área ativa somente mudanças comprovadamente concluídas.
- Usar o comando nativo quando o CLI estiver disponível; caso contrário,
  preservar o pacote completo na estrutura de arquivo OpenSpec, sem modificar
  os artefatos.
- Evitar perda de dados em caso de colisão, validação malsucedida ou erro
  durante o arquivamento.
- Deixar evidência verificável de que o pacote saiu da área ativa e está
  preservado no arquivo nativo.

### Não objetivos

- Restaurar ou editar mudanças existentes, ou arquivar mudanças incompletas.
- Alterar código do produto, configuração, `AGENTS.md` ou o CLI do OpenSpec.
- Arquivar mudanças incompletas, resolver conflitos automaticamente ou
  renomear pacotes para contornar colisões.
- Modificar `restore-archived-openspec-changes` ou mudar sua direção.

## Decisões

1. **Elegibilidade antes de qualquer movimentação.** Exigir que todas as tarefas
   aplicáveis estejam marcadas como concluídas. Para mudanças sem `tasks.md`,
   exigir evidência explícita e verificável de conclusão nos demais artefatos;
   a ausência de tarefas, por si só, não comprova conclusão. Executar a
   validação OpenSpec quando o CLI estiver disponível. Se a conclusão não
   puder ser confirmada, manter a mudança ativa.
2. **Preferir o fluxo nativo, com fallback conservador autorizado.** Quando
   disponível, invocar `openspec archive <change>` e deixar o CLI aplicar as
   convenções da versão instalada. Se o CLI não estiver disponível, mover
   somente o pacote completo elegível para
   `openspec/changes/archive/YYYY-MM-DD-<change>`, após conferir colisões.
   Não editar ou descartar artefatos. Registrar que validação/arquivamento
   nativos não puderam ser executados.
3. **Não sobrescrever em conflitos.** Antes de confirmar, inspecionar se o
   destino nativo já existe ou se a operação reporta colisão de nome/conteúdo.
   Em qualquer conflito, não forçar a operação, não mesclar, não renomear e não
   remover arquivos. Preservar a mudança ativa e o conteúdo encontrado no
   arquivo, registrar o conflito e solicitar resolução explícita.
4. **Verificar após o arquivamento.** Confirmar que o pacote não aparece mais
   na área ativa e que seus artefatos continuam acessíveis no arquivo.
   Comparar a lista/estrutura dos artefatos antes e depois; usar comparação de
   conteúdo quando o comportamento do CLI modificar ou consolidar artefatos.
   Confirmar também que nenhum pacote não selecionado foi alterado.
5. **Falhas parciais permanecem conservadoras.** Se o CLI falhar ou o resultado
   não puder ser confirmado, não tentar uma movimentação manual compensatória.
   O fallback manual aplica-se somente quando o CLI está indisponível antes
   da operação; nunca usar o fallback para contornar falha ambígua do CLI.
6. **Preservar mudanças não selecionadas.** Esta execução arquiva somente
   pacotes comprovadamente concluídos; não altera documentos operacionais nem
   modifica a mudança pendente `restore-archived-openspec-changes`.

## Riscos e compensações

- **Tarefas marcadas incorretamente como concluídas:** validar os artefatos
  antes de aceitar a elegibilidade; manter no diretório ativo em caso de
  dúvida.
- **Mudança inválida ou incompleta:** conclusão explícita é pré-condição;
  validação aprovada também é pré-condição quando o CLI está disponível.
- **Colisão ou arquivo preexistente:** bloquear sem sobrescrever; a resolução
  manual requer inspeção e autorização explícita.
- **Diferenças entre versões do CLI:** usar o mecanismo nativo da versão
  instalada e verificar sua ajuda/documentação antes de confirmar; não assumir
  um caminho de destino customizado.
- **CLI indisponível:** usar o fallback de movimentação documentado somente
  para pacotes com conclusão comprovada; registrar que a validação nativa não
  pôde ser feita.

## Plano de migração

Não há migração de dados de produto. A execução consiste em selecionar uma
mudança concluída, verificar tarefas/evidências, validar pelo CLI se
disponível, inspecionar conflitos e arquivar pelo CLI nativo ou pelo fallback
conservador se o CLI estiver indisponível.

## Verificação

- Confirmar que a validação OpenSpec da mudança selecionada passou quando o
  CLI estiver disponível; se indisponível, registrar explicitamente a limitação.
- Confirmar que o CLI nativo concluiu a operação sem conflito ou, no fallback,
  que somente o pacote elegível foi movido para o destino OpenSpec esperado.
- Confirmar que o pacote deixou de estar ativo e seus artefatos estão no
  arquivo nativo.
- Comparar nomes/estrutura e conteúdo dos artefatos e confirmar que pacotes
  não selecionados permaneceram inalterados.
- Em conflito ou falha ambígua, confirmar que nenhum conteúdo foi sobrescrito
  ou removido e reportar a operação como bloqueada.
