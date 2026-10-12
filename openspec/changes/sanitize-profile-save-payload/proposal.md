## Why

Ao salvar o perfil, o endpoint do Xano retorna “Text filter requires an integer, float, string or boolean value.” A inspeção do endpoint confirmou que `foto_perfil` é texto e que o PUT grava esse campo diretamente; por isso, enviar um arquivo multipart ali ou omitir a chave não é compatível com o contrato atual.

## What Changes

- Normalizar nome, CPF e telefone como strings antes da requisição, removendo caracteres de formatação de CPF e telefone e usando string vazia para valores ausentes.
- Adicionar um endpoint Xano autenticado para receber a nova imagem via multipart, armazená-la como imagem pública e retornar sua URL estável.
- Enviar o arquivo multipart somente ao endpoint de upload; depois salvar o perfil em JSON, com `foto_perfil` como URL string. Sem nova imagem, reenviar a URL persistida ou uma string vazia.
- Preservar os nomes de campo já usados pelo contrato do endpoint (`nome_completo`, `cpf`, `telefone`) e a foto persistida quando nenhuma imagem nova for selecionada.
- Manter o feedback de carregamento durante o salvamento e apresentar a mensagem de sucesso existente somente após uma resposta bem-sucedida.

## Capabilities

### New Capabilities
- `profile/profile-save`: Define a serialização dos campos e da foto no salvamento de perfil, incluindo feedback de sucesso e carregamento.

### Modified Capabilities

## Impact

- **Dentro do MVP:** sim; corrige a edição de perfil já existente.
- **Código afetado:** sanitização em `AuthState.save_profile`, integração de upload e chamadas de perfil em `sosdrive.py`, testes e fonte Xano em `xano/api/authentication/profile/`.
- **API:** mantém `/user_profile` e seus métodos POST/PUT, acrescenta um endpoint autenticado de upload de imagem e usa a URL retornada como string em `foto_perfil`.
- **Reutilização:** reaproveita a seleção e prévia Reflex existentes; adiciona o endpoint e armazenamento Xano necessários porque a implementação atual aceita apenas texto no campo `foto_perfil`.
- **Entidades:** altera apenas dados de cadastro do Motorista e Prestador. Chamado, Tipo de Socorro, Avaliação e Localização não são afetados.
- **Verificação:** testar valores ausentes e formatados, upload multipart separado, payload JSON apenas com strings, foto preservada sem nova seleção, falhas em cada etapa e sucesso ponta a ponta no workspace Xano.
