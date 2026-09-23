# Migração de roles do usuário

A tabela `user` agora aceita `cliente` e `prestador`. Execute esta migração no workspace Xano antes de publicar o enum restrito.

## Pré-checagem

1. Exporte a tabela `user` e conte registros com `role = client`, `role = provider` e valores nulos/desconhecidos.
2. Interrompa a publicação se houver valor desconhecido; ele deve ser corrigido manualmente antes da conversão.

## Conversão

Execute uma operação em lote no Xano:

- `client` -> `cliente`
- `provider` -> `prestador`

Depois consulte novamente a tabela e confirme que todos os registros têm `role` igual a `cliente` ou `prestador`.

## Rollback

Se for necessário restaurar o contrato anterior, faça a conversão inversa:

- `cliente` -> `client`
- `prestador` -> `provider`

Mantenha o backup exportado até a validação do login nos dois tipos de conta. Esta migração não deve alterar nenhuma tabela de chamados, avaliações, localização ou perfis.
