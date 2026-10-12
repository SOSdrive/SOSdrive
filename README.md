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
$env:XANO_API_URL = "https://seu-workspace.xano.io/api:seu-grupo"
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\reflex.exe run
```

Defina `XANO_API_URL` antes de iniciar o Reflex; o login e o cadastro leem essa
configuração quando o backend é iniciado. Abra `http://localhost:3000` no
navegador.

Se as portas padrão estiverem ocupadas, escolha portas livres explicitamente:

```powershell
.venv\Scripts\reflex.exe run --frontend-port 3001 --backend-port 8100
Test-NetConnection -ComputerName localhost -Port 3001
Test-NetConnection -ComputerName localhost -Port 8100
Get-NetTCPConnection -LocalPort 3001,8100 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, OwningProcess
Invoke-WebRequest -Uri http://localhost:3001 -UseBasicParsing
Invoke-WebRequest -Uri http://localhost:8100/_health -UseBasicParsing
```

Confirme `TcpTestSucceeded : True` para ambas e respostas HTTP bem-sucedidas
antes de abrir `http://localhost:3001`. A consulta ao listener identifica o
processo que já ocupa cada porta; se houver conflito, escolha outras portas
livres em vez de encerrar um processo que possa pertencer a outro projeto.

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