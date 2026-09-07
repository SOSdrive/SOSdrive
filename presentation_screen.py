"""SOS Drive - public presentation screen."""

from pathlib import Path

import streamlit as st

from styles import inject_design_system, load_local_asset_data_uri


st.set_page_config(
    page_title="SOS Drive | Assistência quando importa",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_design_system()
assets_dir = Path(__file__).parent / "assets"
illustrations = (
    ("car", load_local_asset_data_uri(assets_dir / "car.png")),
    ("tool", load_local_asset_data_uri(assets_dir / "wheel.png")),
    ("battery", load_local_asset_data_uri(assets_dir / "battery.webp")),
)
illustration_markup = "".join(
    f'<img class="sos-float sos-float-{name}" src="{uri}" alt="" aria-hidden="true">'
    for name, uri in illustrations
    if uri
)

with st.container():
    st.markdown(
        f"""
        <section class="sos-hero" aria-label="Apresentação SOS Drive">
          <div class="sos-glow sos-glow-orange"></div>
          <div class="sos-glow sos-glow-blue"></div>
          {illustration_markup}
          <div class="sos-hero-content">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;">
              <div class="sos-brand"><span class="sos-brand-mark">✦</span> SOS drive</div>
              <div class="sos-top-pill">assistência que chega até você</div>
            </div>
            <div class="sos-eyebrow">quando imprevistos acontecem</div>
            <div class="sos-layout">
              <div>
                <h1 class="sos-hero-title">Respire.<br><em>A ajuda</em><br>está chegando.</h1>
                <p class="sos-hero-copy">A SOS Drive encontra assistência confiável perto de você e transforma um momento difícil em um próximo passo simples.</p>
                <div class="sos-trust-row">
                  <span class="sos-chip">◉ localização inteligente</span>
                  <span class="sos-chip">✓ profissionais verificados</span>
                  <span class="sos-chip">↗ acompanhamento claro</span>
                </div>
              </div>
              <div class="sos-visual">
                <div class="sos-visual-top"><span>visão da assistência</span><span class="sos-live">● online</span></div>
                <div class="sos-map"><span class="sos-map-label">Sua localização atual</span></div>
                <div class="sos-glass-panel sos-assist-card">
                  <div class="sos-assist-icon">↗</div>
                  <div><strong>Ajuda a caminho</strong><small>Especialista mais próximo · 12 min</small></div>
                </div>
                <div class="sos-mini-stats"><strong>3</strong> opções encontradas</div>
              </div>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    action, secondary = st.columns([1.15, 1], gap="small")
    with action:
        if st.button("Conhecer a SOS Drive", type="primary", icon=":material/arrow_forward:", width="stretch"):
            st.session_state["presentation_started"] = True
            st.toast("Tudo certo. A Home Operacional está pronta para você.", icon=":material/check_circle:")
    with secondary:
        st.button("Ver como funciona", icon=":material/play_circle:", width="stretch")

st.markdown('<div class="sos-section-kicker">uma jornada mais leve</div>', unsafe_allow_html=True)
st.markdown('<div class="sos-section-title">Do problema à solução, sem labirinto.</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="sos-section-intro">Em poucos passos, você entende as opções disponíveis, escolhe o tipo de ajuda e acompanha tudo com mais tranquilidade.</p>',
    unsafe_allow_html=True,
)
step_one, step_two, step_three = st.columns(3, gap="medium")

for column, number, title, copy in (
    (step_one, "01", "Conte o que aconteceu", "Escolha o tipo de problema com poucos toques e sem formulários longos."),
    (step_two, "02", "Encontre a melhor opção", "Veja profissionais disponíveis na região, com distância e estimativa de chegada."),
    (step_three, "03", "Acompanhe com clareza", "Saiba o que acontece em cada etapa até o atendimento ser concluído."),
):
    with column:
        st.markdown(
            f'<div class="sos-step-card"><div class="sos-step-number">{number} · simples assim</div><h3>{title}</h3><p>{copy}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="sos-section-kicker">assistência para o que você precisa</div>', unsafe_allow_html=True)
st.markdown('<div class="sos-section-title">Quando o carro para, você continua.</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="sos-section-intro">A SOS Drive organiza a situação e conecta você ao suporte certo para os imprevistos mais comuns na estrada.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="sos-service-grid">
      <div class="sos-service"><span>⚙</span><strong>Pane mecânica</strong></div>
      <div class="sos-service"><span>◒</span><strong>Pneu furado</strong></div>
      <div class="sos-service"><span>⚡</span><strong>Bateria</strong></div>
      <div class="sos-service"><span>◉</span><strong>Combustível</strong></div>
      <div class="sos-service"><span>＋</span><strong>Outro problema</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="sos-trust-band">
      <strong>Feita para momentos em que clareza importa.</strong>
      <div class="sos-trust-metric"><b>24h</b><span>acesso quando precisar</span></div>
      <div class="sos-trust-metric"><b>1 lugar</b><span>para pedir e acompanhar</span></div>
      <div class="sos-trust-metric"><b>0 drama</b><span>menos etapas desnecessárias</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="sos-section-kicker">por que escolher a SOS Drive</div>', unsafe_allow_html=True)
st.markdown('<div class="sos-section-title">Informação que deixa tudo mais simples.</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="sos-info-grid">
      <div class="sos-info-card"><div class="sos-info-icon">01</div><h3>Localização inteligente</h3><p>Encontramos opções próximas usando a sua localização, com transparência sobre distância e chegada.</p></div>
      <div class="sos-info-card"><div class="sos-info-icon">02</div><h3>Escolha sem pressão</h3><p>Veja o que está disponível e avance com uma linguagem direta, sem excesso de telas ou termos técnicos.</p></div>
      <div class="sos-info-card"><div class="sos-info-icon">03</div><h3>Acompanhamento claro</h3><p>Entenda o status do atendimento e saiba qual é o próximo passo enquanto a ajuda se aproxima.</p></div>
      <div class="sos-info-card"><div class="sos-info-icon">04</div><h3>Experiência humana</h3><p>Uma interface calma para apoiar decisões rápidas, inclusive em telas pequenas e sob estresse.</p></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="sos-section-title">Perguntas rápidas</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="sos-faq">
      <div class="sos-faq-item"><strong>Preciso instalar alguma coisa?</strong><span>Não. A SOS Drive funciona no navegador do celular ou computador.</span></div>
      <div class="sos-faq-item"><strong>Como a localização é usada?</strong><span>Ela ajuda a encontrar assistência próxima e só é solicitada quando necessária.</span></div>
      <div class="sos-faq-item"><strong>Posso acompanhar o chamado?</strong><span>Sim. Depois de iniciar, você visualiza o andamento e as próximas atualizações.</span></div>
      <div class="sos-faq-item"><strong>E se eu não souber o problema?</strong><span>Escolha “Outro problema” e explique a situação no fluxo de solicitação.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown(
        '<div class="sos-bottom-note"><strong>Uma porta de entrada, não um labirinto.</strong><br><span>Quando quiser testar o fluxo, abra a Home Operacional no menu lateral.</span></div>',
        unsafe_allow_html=True,
    )

if st.session_state.get("presentation_started"):
    st.success("Apresentação concluída. Abra a Home Operacional para iniciar uma solicitação.", icon=":material/check_circle:")
