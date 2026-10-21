## 1. Eligibility and preflight

- [x] 1.1 (reutilizar os artefatos OpenSpec existentes) Inventariar as mudanças
  ativas, conferir todos os checkboxes de tarefas e manter mudanças taskless
  sem evidência explícita de conclusão fora da seleção.
- [ ] 1.2 (validação nativa) Executar `openspec validate` para a mudança e
  registrar o resultado. Bloqueado nesta execução: o comando `openspec` não
  está instalado/disponível, portanto não se declara validação nativa aprovada.
- [x] 1.3 (inspeção sem alteração) Confirmar a indisponibilidade do CLI,
  inspecionar o formato de arquivo adotado (`archive/YYYY-MM-DD-<change>`) e
  verificar que nenhum destino selecionado já existia.

## 2. Native archive

- [x] 2.1 (reutilizar o CLI OpenSpec existente quando disponível) Como o CLI
  está indisponível, usar o fallback autorizado: mover somente pacotes
  elegíveis, completos e intactos para o diretório de arquivo datado OpenSpec.
- [x] 2.2 (preservação de dados) Conferir colisões antes da movimentação;
  nenhuma colisão foi encontrada. Não sobrescrever, mesclar, descartar ou
  renomear conteúdo.

## 3. Verification

- [x] 3.1 (verificação da estrutura existente) Confirmar que cada pacote
  selecionado saiu de `openspec/changes/` e existe no diretório de arquivo
  datado, e que mudanças incompletas/pendentes continuam ativas.
- [x] 3.2 (verificação de integridade) Comparar a estrutura e hashes SHA-256
  de todos os arquivos dos pacotes antes/depois; confirmar ausência de
  colisões e preservação dos pacotes não selecionados.
- [ ] 3.3 (validação OpenSpec) Validar os artefatos conforme o fluxo nativo.
  Bloqueado: CLI indisponível; registrar a limitação sem declarar a validação
  concluída.
