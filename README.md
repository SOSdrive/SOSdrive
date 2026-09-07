# SOS Drive

Experiência web mobile-first em Python + Streamlit para conectar motoristas a assistência veicular.

## Começar pelo lugar certo

A primeira tela é uma apresentação pública, pensada para explicar o serviço e gerar confiança. A operação acontece separadamente na Home interna.

```text
SOSdrive/
├── presentation_screen.py       # 1. Apresentação pública
├── styles.py                     # Tokens e CSS compartilhados
├── assets/                       # Ilustrações locais opcionais (PNG/WebP)
├── requirements.txt             # Dependências Python
├── setup.ps1                    # Instalação no Windows
└── openspec/                   # Propostas e especificações
```

## Executar

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\streamlit.exe run presentation_screen.py
```

Abra o endereço exibido pelo Streamlit, normalmente `http://localhost:8501`.

## Regra de arquitetura

Tudo do frontend é escrito em Python usando Streamlit. Esta versão do projeto
é uma landing pública, sem menu lateral e sem fluxo operacional.

## UX e animações

A apresentação usa recursos do Streamlit instalado no projeto:

- `st.container` e `st.columns` para uma composição responsiva e legível
- `st.html` apenas para o CSS de movimento visual da apresentação
- `st.toast` para feedback imediato após o CTA
- Ícones Material nos controles para reduzir dependência de emojis
- `prefers-reduced-motion` para respeitar usuários que preferem menos animação

O módulo `styles.py` concentra os tokens de cor e os estilos de glow, glassmorphism,
chips, foco, responsividade e movimento. Ilustrações em `assets/` são opcionais e
carregadas localmente como data URI; a ausência delas não impede a aplicação de iniciar.