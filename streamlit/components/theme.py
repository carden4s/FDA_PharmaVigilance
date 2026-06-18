# Shared dark theme, Spanish-friendly styling, and UI helpers
# Co-authored with CoCo
"""Dark theme + CSS for all pages, plus hero() and note() helpers."""
import streamlit as st

ACCENT = "#58a6ff"


def apply_theme():
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
      .stApp { background: radial-gradient(1200px 600px at 20% -10%, #11203a 0%, #0d1117 55%); }
      .block-container { padding-top: 2rem; max-width: 1300px; }
      h1,h2,h3,h4,h5,h6 { color:#e6edf3 !important; font-weight:700; letter-spacing:-0.01em; }
      p, span, label, li { color:#c9d1d9; }

      div[data-testid="stMetric"] {
        background: linear-gradient(135deg,#1c2330 0%,#141a22 100%);
        border:1px solid #2d3340; border-radius:14px; padding:18px 20px;
        box-shadow:0 4px 14px rgba(0,0,0,0.30);
        transition: transform .15s ease, border-color .15s ease;
      }
      div[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color:#3b82f6; }
      div[data-testid="stMetric"] label p {
        color:#8b949e !important; font-weight:600; text-transform:uppercase;
        font-size:.72rem; letter-spacing:.04em;
      }
      div[data-testid="stMetricValue"] { color:#58a6ff !important; font-weight:700; }

      section[data-testid="stSidebar"] { background:#0b0f14; border-right:1px solid #21262d; }
      section[data-testid="stSidebar"] * { color:#c9d1d9; }
      .sb-brand { font-size:1.3rem; font-weight:700; color:#e6edf3; margin-bottom:2px; }
      .sb-sub { color:#8b949e; font-size:.8rem; margin-bottom:6px; }
      .sb-card {
        background:#11161d; border:1px solid #21262d; border-radius:12px;
        padding:14px 16px; margin-top:12px; font-size:.85rem; color:#9aa7b3; line-height:1.5;
      }
      .badge {
        display:inline-block; background:#1f6feb22; color:#79c0ff; border:1px solid #1f6feb55;
        border-radius:999px; padding:3px 11px; font-size:.72rem; font-weight:600; margin:3px 4px 3px 0;
      }

      .stTabs [data-baseweb="tab-list"] { gap:8px; }
      .stTabs [data-baseweb="tab"] {
        background:#11161d; border:1px solid #21262d; border-radius:10px 10px 0 0;
        padding:8px 16px; color:#c9d1d9;
      }
      .stTabs [aria-selected="true"] {
        background:#1f6feb22 !important; color:#79c0ff !important; border-color:#1f6feb55 !important;
      }

      .stDataFrame { border:1px solid #21262d; border-radius:12px; }

      .hero {
        background:linear-gradient(110deg,#1f6feb33 0%,#161b22 65%);
        border:1px solid #2d3340; border-radius:18px; padding:24px 30px; margin-bottom:16px;
      }
      .hero h1 { margin:0; font-size:2rem; color:#e6edf3; }
      .hero p { color:#9aa7b3; margin:8px 0 0 0; font-size:.95rem; }

      .note {
        background:#11161d; border-left:3px solid #58a6ff; border-radius:8px;
        padding:10px 14px; color:#9aa7b3; font-size:.85rem; margin:8px 0;
      }
    </style>
    """, unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


def note(text: str):
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)