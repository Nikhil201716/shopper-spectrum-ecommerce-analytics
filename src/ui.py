from __future__ import annotations

import html

import streamlit as st


def apply_branding() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root { --ink:#eaf2ff; --muted:#9fb0c9; --navy:#07111f; --panel:#0d1b2d; --mint:#17c3b2; --blue:#4f7cff; --gold:#f6c85f; --coral:#ff6b6b; }
        html, body, [class*="css"] { font-family:'DM Sans','Segoe UI',sans-serif; }
        .stApp { background: radial-gradient(circle at 10% 0%, rgba(79,124,255,.16), transparent 30%), radial-gradient(circle at 100% 15%, rgba(23,195,178,.12), transparent 26%), #07111f; color:var(--ink); }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#0b1829,#07111f); border-right:1px solid rgba(148,163,184,.14); }
        h1,h2,h3 { font-family:'Space Grotesk','Segoe UI',sans-serif !important; letter-spacing:-.035em; }
        .hero { position:relative; overflow:hidden; padding:2.4rem 2.5rem; margin:.2rem 0 1.4rem; border:1px solid rgba(127,157,204,.22); border-radius:24px; background:linear-gradient(135deg,rgba(79,124,255,.18),rgba(23,195,178,.08) 55%,rgba(246,200,95,.06)); box-shadow:0 20px 60px rgba(0,0,0,.22); }
        .hero:after { content:''; position:absolute; width:220px; height:220px; right:-80px; top:-100px; border-radius:50%; background:radial-gradient(circle,rgba(23,195,178,.28),transparent 68%); }
        .eyebrow { color:var(--mint); font-weight:700; letter-spacing:.14em; text-transform:uppercase; font-size:.77rem; }
        .hero h1 { margin:.45rem 0 .55rem; font-size:clamp(2.1rem,5vw,4rem); line-height:1.02; max-width:920px; }
        .hero p { color:#b8c6db; font-size:1.04rem; line-height:1.65; max-width:860px; margin:0; }
        .insight-card { min-height:150px; padding:1.2rem 1.25rem; border-radius:18px; background:linear-gradient(160deg,rgba(20,37,60,.96),rgba(10,25,43,.96)); border:1px solid rgba(148,163,184,.17); box-shadow:0 14px 34px rgba(0,0,0,.18); }
        .insight-card .label { color:var(--mint); font-size:.72rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
        .insight-card .text { color:#e9f1fc; margin-top:.55rem; line-height:1.55; }
        .scope-pill { display:inline-block; padding:.32rem .64rem; margin:.1rem .2rem .1rem 0; border-radius:999px; font-size:.75rem; color:#c7d5ea; border:1px solid rgba(148,163,184,.22); background:rgba(15,31,52,.7); }
        [data-testid="stMetric"] { background:linear-gradient(145deg,rgba(16,34,56,.96),rgba(9,24,41,.96)); border:1px solid rgba(148,163,184,.16); border-radius:16px; padding:1rem 1.1rem; box-shadow:0 10px 28px rgba(0,0,0,.16); }
        [data-testid="stMetricLabel"] { color:#aebed4; }
        [data-testid="stMetricValue"] { font-family:'Space Grotesk',sans-serif; }
        .stTabs [data-baseweb="tab-list"] { gap:.5rem; }
        .stTabs [data-baseweb="tab"] { border-radius:999px; padding:.55rem 1rem; background:rgba(15,31,52,.75); }
        .stTabs [aria-selected="true"] { background:linear-gradient(90deg,#4f7cff,#17c3b2) !important; color:white !important; }
        div[data-testid="stDataFrame"] { border:1px solid rgba(148,163,184,.18); border-radius:15px; overflow:hidden; }
        .stButton>button, .stDownloadButton>button { border:0; border-radius:12px; font-weight:700; background:linear-gradient(90deg,#4f7cff,#17c3b2); color:white; box-shadow:0 8px 24px rgba(79,124,255,.22); }
        .stButton>button:hover, .stDownloadButton>button:hover { filter:brightness(1.08); color:white; }
        code { color:#a7f3e8 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="hero">
          <div class="eyebrow">{html.escape(kicker)}</div>
          <h1>{html.escape(title)}</h1>
          <p>{html.escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def insight_card(label: str, text: str) -> None:
    st.markdown(
        f"<div class='insight-card'><div class='label'>{html.escape(label)}</div><div class='text'>{html.escape(text)}</div></div>",
        unsafe_allow_html=True,
    )


def scope_pills(*items: str) -> None:
    pills = "".join(f"<span class='scope-pill'>{html.escape(item)}</span>" for item in items)
    st.markdown(pills, unsafe_allow_html=True)

