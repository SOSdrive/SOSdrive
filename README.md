# SOS Drive

Experiência web mobile-first em Python + Streamlit para conectar motoristas a assistência veicular.

## Começar pelo lugar certo

A primeira tela é uma apresentação pública, pensada para explicar o serviço e gerar confiança. A operação acontece separadamente na Home interna.

```text
SOSdrive/
├── presentation_screen.py       # 1. Apresentação pública
├── styles.py                     # Tokens e CSS compartilhados
├── assets/                       # Ilustrações locais opcionais (PNG/WebP)
├── pages/
│   └── 1_Home_Operacional.py    # 2. Home interna pós-login
├── requirements.txt             # Dependências Python
├── setup.ps1                     # Instalação no Windows
├── SETUP_STREAMLIT.md            # Guia didático
└── openspec/changes/add-home-screen/
	├── proposal.md               # Por que construir
	├── design.md                 # Como organizar tecnicamente
	├── specs/                    # Comportamentos esperados
	└── tasks.md                  # Checklist de implementação
```

## Executar

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\streamlit.exe run presentation_screen.py
```

Abra `http://localhost:8501`. Use o menu lateral **Home Operacional** para testar mapa, GPS, atalhos e estados do fluxo interno.

## Regra de arquitetura

Tudo do frontend é escrito em Python usando Streamlit. A tela de apresentação não contém mapa, prestadores ou navegação operacional; esses elementos pertencem exclusivamente à Home interna.

## UX e animações

A apresentação usa recursos do Streamlit instalado no projeto:

- `st.container` e `st.columns` para uma composição responsiva e legível
- `st.html` apenas para o CSS de movimento visual da apresentação
- `st.toast` para feedback imediato após o CTA
- Ícones Material nos controles para reduzir dependência de emojis
- `prefers-reduced-motion` para respeitar usuários que preferem menos animação

O módulo `styles.py` concentra os tokens de cor e os estilos de glow, glassmorphism,
chips, foco, responsividade e movimento. A Home Operacional pode importá-lo sem
importar conteúdo da landing. Ilustrações em `assets/` são opcionais e carregadas
localmente como data URI; a ausência delas não impede a aplicação de iniciar.