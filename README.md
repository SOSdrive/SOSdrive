# SOS Drive

Experiência web mobile-first em Python + Reflex para conectar motoristas a assistência veicular.

## Começar pelo lugar certo

A primeira tela é uma apresentação pública, pensada para explicar o serviço e gerar confiança. A operação acontece separadamente na Home interna.

```text
SOSdrive/
├── sosdrive.py                  # Lógica da aplicação Reflex
├── sosdrive_app/                # Entry point do projeto Reflex
├── styles.py                     # Tokens e CSS compartilhados
├── assets/                       # Ilustrações locais opcionais (PNG/WebP)
├── requirements.txt             # Dependências Python
├── setup.ps1                    # Instalação no Windows
└── openspec/                   # Propostas e especificações
```

## Executar

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\reflex.exe run
```

Abra `http://localhost:3000` no navegador.

Para habilitar login e cadastro, configure a URL base da API Xano no ambiente:

```powershell
$env:XANO_API_URL = "https://seu-workspace.xano.io/api:seu-grupo"
```

## Regra de arquitetura

Tudo do frontend é escrito em Python usando Reflex. Esta versão do projeto
é uma landing pública, sem menu lateral e sem fluxo operacional.

## UX e animações

A apresentação usa componentes e estado do Reflex:

- componentes Reflex para uma composição responsiva e legível
- CSS global Reflex para o movimento visual da apresentação
- estado Reflex para navegação e feedback do login
- `prefers-reduced-motion` para respeitar usuários que preferem menos animação

O módulo `styles.py` concentra os tokens de cor e os estilos globais Reflex.
Ilustrações em `assets/` são opcionais e a ausência delas não impede a aplicação de iniciar.