"""Shared visual tokens and CSS helpers for SOS Drive Streamlit screens."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


COLORS = {
    "trust_blue": "#1E3A8A",
    "navy": "#102A43",
    "emergency_orange": "#F97316",
    "orange_dark": "#C2410C",
    "success_green": "#16A34A",
    "background": "#F3F4F6",
    "surface": "#FFFFFF",
    "text": "#111827",
    "muted": "#64748B",
    "line": "#E2E8F0",
}


def load_local_asset_data_uri(asset_path: str | Path, max_bytes: int = 1_000_000) -> str | None:
    """Return a local PNG/WebP as a data URI, or None when it is unavailable."""
    path = Path(asset_path)
    if path.suffix.lower() not in {".png", ".webp"} or not path.is_file():
        return None
    if path.stat().st_size > max_bytes:
        return None
    mime = "image/png" if path.suffix.lower() == ".png" else "image/webp"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inject_design_system() -> None:
    """Inject scoped reusable styles for the landing and future Streamlit screens."""
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebar"],
            [data-testid="stSidebarCollapseButton"],
            [data-testid="collapsedControl"] {{ display: none !important; }}

            :root {{
          --sos-blue: {COLORS["trust_blue"]};
          --sos-navy: {COLORS["navy"]};
          --sos-orange: {COLORS["emergency_orange"]};
          --sos-orange-dark: {COLORS["orange_dark"]};
          --sos-bg: {COLORS["background"]};
          --sos-text: {COLORS["text"]};
          --sos-muted: {COLORS["muted"]};
        }}
        .stApp {{
          background:
            radial-gradient(circle at 12% 4%, rgba(249,115,22,.08), transparent 28rem),
            {COLORS["background"]};
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        .block-container {{ max-width: 1240px; padding: 1.5rem 2.5rem 5rem; font-family: Inter, Poppins, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
        .block-container p {{ letter-spacing: -.01em; }}
        .sos-hero {{
          position: relative; isolation: isolate; overflow: hidden;
          border-radius: 34px; padding: 2rem 2rem 2.3rem;
          background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(248,250,252,.72));
          border: 1px solid rgba(255,255,255,.75);
        }}
        .sos-glow {{
          position: absolute; z-index: -1; width: 22rem; height: 22rem;
          border-radius: 50%; filter: blur(88px); pointer-events: none;
          animation: sos-pulse-glow 7s ease-in-out infinite;
        }}
        .sos-glow-orange {{ top: -13rem; left: -8rem; background: rgba(249,115,22,.34); }}
        .sos-glow-blue {{
          right: -10rem; bottom: -14rem; background: rgba(30,58,138,.3);
          animation-delay: -3.5s;
        }}
        .sos-hero-content {{ position: relative; z-index: 1; }}
        .sos-layout {{ display: grid; grid-template-columns: minmax(0, 1.02fr) minmax(320px, .98fr); gap: 2.5rem; align-items: center; }}
        .sos-brand {{ display: flex; align-items: center; gap: .7rem; color: var(--sos-text); font-weight: 900; letter-spacing: -.04em; font-size: 1.2rem; }}
        .sos-brand-mark {{ display: grid; place-items: center; width: 2.45rem; height: 2.45rem; color: white; background: var(--sos-navy); border-radius: 12px; box-shadow: 0 8px 18px rgba(16,42,67,.22); }}
        .sos-top-pill {{ border: 1px solid rgba(30,58,138,.15); background: rgba(255,255,255,.55); border-radius: 999px; color: var(--sos-navy); font-weight: 800; font-size: .78rem; padding: .55rem .85rem; }}
        .sos-eyebrow {{ color: var(--sos-blue); font-weight: 900; letter-spacing: .16em; text-transform: uppercase; font-size: .72rem; margin: 4.5rem 0 1rem; }}
        .sos-hero-title {{ color: var(--sos-text) !important; font-size: clamp(3.2rem, 7vw, 5.5rem); line-height: .94; font-weight: 850; letter-spacing: -.06em; margin: 0 0 1.35rem; }}
        .sos-hero-title em {{ color: var(--sos-orange); font-style: normal; }}
        .sos-hero-copy {{ color: var(--sos-muted); font-size: 1.12rem; line-height: 1.6; max-width: 590px; }}
        .sos-trust-row {{ display: flex; flex-wrap: wrap; gap: .65rem; color: var(--sos-navy); font-size: .8rem; font-weight: 800; margin: 1.3rem 0 1.7rem; }}
        .sos-chip {{ background: rgba(255,255,255,.58); border: 1px solid rgba(30,58,138,.14); border-radius: 999px; padding: .58rem .78rem; box-shadow: 0 6px 18px rgba(15,23,42,.04); backdrop-filter: blur(10px); transition: transform .2s ease, box-shadow .2s ease; }}
        .sos-chip:hover {{ transform: translateY(-3px); box-shadow: 0 12px 24px rgba(15,23,42,.12); }}
        .sos-visual {{ position: relative; min-height: 445px; overflow: hidden; border-radius: 28px; padding: 1.2rem; color: white; background: rgba(16,42,67,.92); box-shadow: 0 28px 70px rgba(15,23,42,.2); }}
        .sos-visual::before {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 80% 0%, rgba(56,189,248,.28), transparent 36%), linear-gradient(145deg, rgba(16,42,67,.88), rgba(30,58,138,.85)); }}
        .sos-glass-panel {{ background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.18); border-radius: 22px; box-shadow: 0 24px 65px rgba(2,12,27,.28); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }}
        .sos-visual > * {{ position: relative; z-index: 1; }}
        .sos-visual-top {{ display: flex; justify-content: space-between; color: #C8E7FA; font-size: .7rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }}
        .sos-live {{ color: #86EFAC; }}
        .sos-map {{ position: relative; height: 235px; margin: 1.25rem 0; overflow: hidden; border: 1px solid rgba(255,255,255,.14); border-radius: 22px; background: linear-gradient(32deg, transparent 47%, rgba(255,255,255,.12) 48%, transparent 50%), linear-gradient(140deg, transparent 46%, rgba(255,255,255,.1) 47%, transparent 49%), #1B4A70; }}
        .sos-map::after {{ content: ""; position: absolute; left: 52%; top: 47%; width: 1.15rem; height: 1.15rem; border: 5px solid white; border-radius: 50%; background: var(--sos-orange); box-shadow: 0 0 0 13px rgba(249,115,22,.18), 0 0 0 27px rgba(249,115,22,.08); animation: sos-pulse 2.2s ease-in-out infinite; }}
        .sos-map-label {{ position: absolute; left: 1rem; bottom: 1rem; z-index: 1; padding: .55rem .7rem; border-radius: 10px; background: rgba(11,18,32,.58); font-size: .75rem; font-weight: 700; }}
        .sos-assist-card {{ display: flex; align-items: center; gap: .8rem; padding: .95rem 1rem; }}
        .sos-assist-icon {{ display: grid; place-items: center; width: 2.55rem; height: 2.55rem; color: var(--sos-navy); background: var(--sos-orange); border-radius: 13px; font-size: 1.2rem; }}
        .sos-assist-card strong {{ display: block; font-size: .95rem; }}
        .sos-assist-card small {{ color: #C8E7FA; }}
        .sos-mini-stats {{ position: absolute !important; right: 1.2rem; bottom: 1.2rem; padding: .7rem .85rem; color: var(--sos-navy); background: white; border-radius: 14px; font-size: .72rem; box-shadow: 0 12px 25px rgba(0,0,0,.15); }}
        .sos-float {{ position: absolute !important; z-index: 2 !important; pointer-events: none; filter: drop-shadow(0 18px 16px rgba(15,23,42,.2)); animation: sos-float 4.3s ease-in-out infinite; }}
        .sos-float-car {{ right: 2%; top: 15%; width: 4.4rem; animation-delay: -.7s; }}
        .sos-float-tool {{ left: 46%; top: 5%; width: 3.3rem; animation-delay: -2.2s; animation-duration: 3.7s; }}
        .sos-float-battery {{ right: 10%; bottom: 16%; width: 3rem; animation-delay: -1.4s; animation-duration: 4.8s; }}
        .sos-section-kicker {{ color: var(--sos-orange); font-weight: 900; font-size: .75rem; letter-spacing: .13em; text-transform: uppercase; }}
        .sos-section-title {{ color: var(--sos-text) !important; font-size: 2rem; font-weight: 900; letter-spacing: -.05em; }}
        .sos-section-intro {{ color: var(--sos-muted); max-width: 650px; font-size: 1.04rem; line-height: 1.65; margin: .45rem 0 1.4rem; }}
        .sos-info-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .8rem; margin: 1.3rem 0 3.2rem; }}
        .sos-info-card {{ min-height: 145px; padding: 1.15rem; border: 1px solid rgba(226,232,240,.9); border-radius: 20px; background: rgba(255,255,255,.8); box-shadow: 0 10px 24px rgba(15,23,42,.04); transition: transform .2s ease, box-shadow .2s ease; }}
        .sos-info-card:hover {{ transform: translateY(-4px); box-shadow: 0 16px 30px rgba(15,23,42,.1); }}
        .sos-info-icon {{ display: grid; place-items: center; width: 2.25rem; height: 2.25rem; color: white; background: var(--sos-blue); border-radius: 11px; font-weight: 900; }}
        .sos-info-card h3 {{ color: var(--sos-text) !important; margin: .8rem 0 .35rem; font-size: 1rem; }}
        .sos-info-card p {{ color: var(--sos-muted); margin: 0; font-size: .86rem; line-height: 1.5; }}
        .sos-service-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .75rem; margin: 1.1rem 0 3.2rem; }}
        .sos-service {{ padding: 1rem .8rem; text-align: center; border: 1px solid rgba(226,232,240,.9); border-radius: 18px; background: rgba(255,255,255,.72); }}
        .sos-service strong {{ display: block; color: var(--sos-text); margin-top: .6rem; font-size: .86rem; }}
        .sos-service span {{ display: grid; place-items: center; width: 2.7rem; height: 2.7rem; margin: auto; color: var(--sos-orange); background: #FFF7ED; border-radius: 14px; font-size: 1.25rem; }}
        .sos-trust-band {{ display: grid; grid-template-columns: 1.2fr repeat(3, 1fr); gap: 1rem; align-items: center; margin: 0 0 2rem; padding: 1.35rem; border-radius: 22px; color: white; background: linear-gradient(135deg, var(--sos-navy), var(--sos-blue)); box-shadow: 0 18px 36px rgba(30,58,138,.2); }}
        .sos-trust-band strong {{ font-size: 1.05rem; }}
        .sos-trust-metric {{ border-left: 1px solid rgba(255,255,255,.22); padding-left: 1rem; }}
        .sos-trust-metric b {{ display: block; font-size: 1.4rem; }}
        .sos-trust-metric span {{ color: #C8E7FA; font-size: .76rem; }}
        .sos-faq {{ display: grid; grid-template-columns: 1fr 1fr; gap: .8rem; margin: 1.1rem 0 2.5rem; }}
        .sos-faq-item {{ padding: 1rem 1.1rem; border-bottom: 1px solid var(--sos-line, #E2E8F0); }}
        .sos-faq-item strong {{ color: var(--sos-text); display: block; margin-bottom: .35rem; }}
        .sos-faq-item span {{ color: var(--sos-muted); font-size: .88rem; line-height: 1.5; }}
        .sos-step-card {{ min-height: 165px; padding: 1.2rem; border: 1px solid rgba(226,232,240,.9); border-radius: 20px; background: rgba(255,255,255,.78); box-shadow: 0 10px 24px rgba(15,23,42,.04); }}
        .sos-step-card h3 {{ color: var(--sos-text) !important; margin: .65rem 0 .45rem; font-size: 1.05rem; }}
        .sos-step-card p {{ color: var(--sos-muted); line-height: 1.55; font-size: .9rem; }}
        .sos-step-number {{ color: var(--sos-orange); font-weight: 950; font-size: .76rem; letter-spacing: .12em; }}
        .sos-bottom-note {{ border-radius: 22px; padding: 1.25rem; background: var(--sos-navy); color: white; }}
        .sos-bottom-note span {{ color: #C8E7FA; font-size: .9rem; }}
        div.stButton > button {{ min-height: 3.25rem; border-radius: 14px; border: 0; font-weight: 850; transition: transform .2s ease, box-shadow .2s ease; }}
        div.stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 10px 22px rgba(15,23,42,.13); }}
        div.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, var(--sos-orange), #FB923C); color: var(--sos-navy); box-shadow: 0 12px 26px rgba(249,115,22,.3); }}
        div.stButton > button:focus-visible {{ outline: 3px solid #38BDF8; outline-offset: 3px; }}
        @keyframes sos-pulse-glow {{ 0%,100% {{ transform: scale(1); opacity: .75; }} 50% {{ transform: scale(1.08); opacity: 1; }} }}
        @keyframes sos-pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.12); }} }}
        @keyframes sos-float {{ 0%,100% {{ transform: translateY(0) rotate(-3deg); }} 50% {{ transform: translateY(-13px) rotate(4deg); }} }}
        @media (max-width: 700px) {{
          .block-container {{ padding: 1rem 1rem 2.5rem; }}
          .sos-hero {{ padding: 1.15rem; border-radius: 25px; }}
          .sos-top-pill {{ display: none; }}
          .sos-eyebrow {{ margin-top: 3rem; }}
          .sos-hero-title {{ font-size: clamp(3rem, 16vw, 4.5rem); }}
          .sos-layout {{ grid-template-columns: 1fr; gap: 1rem; }}
          .sos-visual {{ min-height: 410px; margin-top: 1.5rem; }}
          .sos-map {{ height: 205px; }}
          .sos-float-tool, .sos-float-battery {{ display: none; }}
          .sos-float-car {{ width: 3.2rem; opacity: .8; }}
          .sos-info-grid, .sos-service-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .sos-trust-band {{ grid-template-columns: 1fr 1fr; }}
          .sos-trust-band > strong {{ grid-column: 1 / -1; }}
          .sos-faq {{ grid-template-columns: 1fr; }}
        }}
        @media (prefers-reduced-motion: reduce) {{
          *, *::before, *::after {{ animation: none !important; transition: none !important; transform: none !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
