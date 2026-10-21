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

Crie um arquivo `.env` na raiz do projeto (ao lado de `sosdrive.py`) e
configure a URL base real copiada do grupo de API do seu workspace Xano:

```dotenv
XANO_API_URL=https://<workspace>.xano.io/api:<grupo>
# Opcional se os endpoints de chamados estiverem em outro grupo Xano:
XANO_SERVICES_URL=https://<workspace>.xano.io/api:<grupo-de-servicos>
```

O arquivo `.env` é local e ignorado pelo Git. O backend carrega esse arquivo ao
iniciar; variáveis já exportadas no ambiente têm precedência. Um modelo sem
valores reais está em [`.env.example`](./.env.example).

No macOS/Linux, instale e inicie assim:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/reflex run
```

No Windows/PowerShell, também é possível definir as variáveis diretamente na
sessão:

```powershell
$env:XANO_API_URL = "https://seu-workspace.xano.io/api:seu-grupo"
# Opcional: configure se os endpoints de chamados estiverem em outro grupo Xano.
$env:XANO_SERVICES_URL = "https://seu-workspace.xano.io/api:grupo-de-servicos"
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\reflex.exe run
```

`XANO_API_URL` deve ser a URL base do grupo Xano (incluindo `/api:<grupo>`),
sem o caminho `/auth/login`. Se chamados e mensagens estiverem publicados em
outro grupo, configure `XANO_SERVICES_URL` para esse grupo. Se não estiver
definida, chamados e mensagens usam `XANO_API_URL` como fallback. Reinicie o
backend depois de alterar o `.env`. Abra `http://localhost:3000` no navegador.

Para apresentar em dois computadores na mesma rede Wi-Fi, descubra o IPv4 do
Mac que executará o app e inicie o Reflex usando esse endereço:

```bash
export SOSDRIVE_DEMO_HOST="$(ipconfig getifaddr en0)"
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m reflex run --backend-host 0.0.0.0
```

O terminal precisa continuar aberto. No computador do Mac, e também no do
professor/colega, abra `http://<IP-DO-MAC>:3000` (não use `localhost` no
segundo computador). Os dois computadores devem estar na mesma rede; permita
as conexões de entrada do Python/Node no firewall do macOS. Os usuários devem
entrar com contas diferentes de cliente e prestador, e o cliente precisa ter
um veículo cadastrado. O chamado é criado no Xano configurado no `.env`; use
contas de demonstração e evite dados pessoais/reais.

No workspace Xano SOS Drive já foram publicados os endpoints de aceite,
liberação, conclusão e mensagens, e as tabelas `service_messages` e
`service_request_acceptance` estão presentes. No workspace/grupo usado pelo
`.env`, confirme que as mesmas rotas e schemas foram implantados antes da
apresentação. O painel aberto consulta novas mensagens a cada 2 segundos e
para de consultar quando é fechado. Não publique a rota de mensagens sem as
regras de autorização por participante incluídas nos arquivos Xano.

O teste real de integração exige um workspace Xano descartável com um chamado
pendente pertencente ao cliente de teste, além de tokens para cliente, prestador
que aceitará o chamado, segundo prestador e usuário não participante. Para
evitar gravações acidentais em produção, o teste só executa com
`XANO_TEST_DISPOSABLE_WORKSPACE=true`. Configure localmente essas variáveis no
ambiente ou no arquivo `.env` ignorado pelo Git:
`XANO_TEST_API_URL`, `XANO_TEST_REQUEST_ID`,
`XANO_TEST_CLIENT_TOKEN`, `XANO_TEST_PROVIDER_TOKEN`,
`XANO_TEST_SECOND_PROVIDER_TOKEN` e `XANO_TEST_NONPARTICIPANT_TOKEN`, então
execute `python -m unittest tests.test_service_chat_xano_integration` (ou use
`.venv/bin/python` no macOS/Linux e `.venv\Scripts\python.exe` no Windows). O
teste cria mensagens de verificação e deixa esses registros no workspace
descartável.

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