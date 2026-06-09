"""Shared dark theme + CSS for all pages."""
import streamlit as st

ACCENT = "#58a6ff"


def apply_theme():
    st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        h1, h2, h3, h4, h5, h6 { color: #e6edf3 !important; }
        p, span, label, li { color: #c9d1d9; }
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1e2530 0%, #161b22 100%);
            border: 1px solid #2d3340;
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        }
        div[data-testid="stMetric"] label p { color: #8b949e !important; font-weight: 600; }
        div[data-testid="stMetricValue"] { color: #58a6ff !important; }
        section[data-testid="stSidebar"] { background-color: #161b22; }
        .stTabs [data-baseweb="tab-list"] { gap: 6px; }
        .stTabs [data-baseweb="tab"] { color: #c9d1d9; }
        .hero {
            background: linear-gradient(110deg, #1f6feb22 0%, #161b22 60%);
            border: 1px solid #2d3340; border-radius: 16px;
            padding: 22px 28px; margin-bottom: 14px;
        }
        .hero h1 { margin: 0; font-size: 1.9rem; color: #e6edf3; }
        .hero p { color: #8b949e; margin: 6px 0 0 0; }
    </style>
    """, unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    st.markdown(f"""
    <div class="hero">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)