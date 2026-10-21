# Spec: Perfil de Usuário e Colaborador

## Visão Geral
Define a interface de identificação e edição de perfil para ambos os tipos de conta no sistema.

## Cenários Funcionais

### Avatar de Navegação
**Given** que o usuário está em um dashboard (`/customer` ou `/provider`)
**When** a página é carregada
**Then** um avatar circular deve ser exibido no canto superior direito.
**Then** o avatar deve mostrar a foto do usuário se existir, ou as iniciais do nome em um fundo colorido se não existir.
**When** o avatar é clicado
**Then** o sistema deve redirecionar para `/profile`.

### Edição de Foto
**Given** que o usuário está na tela de perfil (`/profile`)
**When** o usuário clica em "Alterar Foto"
**Then** o sistema deve abrir o seletor de arquivos do sistema.
**When** uma imagem é selecionada
**Then** o sistema deve exibir um preview imediato da imagem.
**When** o usuário salva as alterações
**Then** a imagem deve ser persistida no estado local (`AppState.user_profile_photo`).

### Edição de Dados Básicos
**Given** que o usuário está na tela de perfil (`/profile`)
**When** o usuário altera nome, email ou telefone
**Then** as alterações devem ser refletidas no estado local ao salvar.

## Diferenças por Perfil
- **Cliente**: Vê apenas dados básicos e seção de veículos.
- **Prestador**: Vê dados básicos, seção de especialidades (já existente) e seção de veículos.

---
**Status: Implementado (UI/Estado Local)**
Integração com backend (Xano) prevista para etapa futura.

