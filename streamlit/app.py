import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data.snowflake_client import SnowflakeClient

# ---------- Page config ----------
st.set_page_config(
    page_title="FDA PharmaVigilance",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Enhanced styling ----------
st.markdown("""
<style>
    /* Root palette: clinical dark with cyan accent */
    :root {
        --bg-primary: #0a0e13;
        --bg-secondary: #0f1419;
        --bg-tertiary: #151b24;
        --accent: #06b6d4;
        --danger: #ef4444;
        --success: #10b981;
        --warning: #f59e0b;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --border: #2d3340;
    }

    * {
        margin: 0;
        padding: 0;
    }

    .main {
        background: linear-gradient(135deg, #0a0e13 0%, #0f1419 100%);
        color: var(--text-primary);
    }

    .block-container {
        padding-top: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #0f1419 0%, #151b24 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 32px 40px;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.08) 0%, transparent 70%);
        border-radius: 50%;
    }

    .hero-content {
        position: relative;
        z-index: 1;
    }

    .hero h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }

    .hero p {
        color: var(--text-secondary);
        font-size: 0.95rem;
        margin: 0;
        font-weight: 500;
    }

    /* Drug name emphasis */
    .drug-title {
        color: var(--accent);
        font-weight: 700;
    }

    /* Metrics section */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0f1419 0%, #151b24 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: var(--accent);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.1);
        transform: translateY(-2px);
    }

    div[data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-weight: 600;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    div[data-testid="stMetricValue"] {
        color: var(--accent) !important;
        font-weight: 700;
        font-size: 2rem !important;
    }

    /* Typography hierarchy */
    h1 { color: var(--text-primary); font-weight: 700; margin-top: 1.5rem !important; }
    h2 { color: var(--text-primary); font-weight: 700; margin-top: 1.2rem !important; }
    h3 { color: var(--text-secondary); font-weight: 600; margin-top: 1rem !important; }

    /* Subheader styling */
    [data-testid="stSubheader"] {
        border-bottom: 2px solid var(--accent);
        padding-bottom: 0.8rem !important;
        font-size: 1.4rem !important;
        letter-spacing: -0.01em;
    }

    /* Divider enhancement */
    hr {
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        border: none;
        height: 1px;
        margin: 2rem 0 !important;
    }

    /* Tab styling */
    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--accent) !important;
    }

    [data-testid="stTabs"] [aria-selected="true"] button {
        border-bottom: 2px solid var(--accent) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #151b24 100%);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        border-bottom: 2px solid var(--accent);
        padding-bottom: 0.8rem;
    }

    /* Selectbox styling */
    [data-testid="stSelectbox"] > div:first-child {
        border-color: var(--border) !important;
    }

    [data-testid="stSelectbox"] > div:first-child:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1) !important;
    }

    /* Data table styling */
    [data-testid="stDataFrame"] {
        background: var(--bg-secondary) !important;
    }

    [data-testid="stDataFrame"] table {
        font-size: 0.9rem;
    }

    /* Caption styling */
    [data-testid="stCaption"] {
        color: var(--text-secondary);
        font-size: 0.85rem;
    }

    /* Info/warning boxes */
    [data-testid="stInfo"], [data-testid="stWarning"], [data-testid="stError"] {
        border-radius: 12px;
        border-left: 4px solid var(--accent);
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero {
            padding: 24px 20px;
        }

        .hero h1 {
            font-size: 1.8rem;
        }

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <div class="hero-content">
    <h1>💊 FDA PharmaVigilance</h1>
    <p>Real-time adverse event monitoring for pharmaceutical safety · openFDA data · 3-year rolling analysis</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- Data ----------
client = SnowflakeClient()
drugs = client.get_drugs()

if not drugs:
    st.error("⚠️ No data available. Verify Snowflake connection and gold tables in FARMACEUTICADATA.FDA_EXPERIENCE.")
    st.stop()

with st.sidebar:
    st.header("⚙️ Configuration")
    selected_drug = st.selectbox("Select drug to analyze", drugs)
    st.caption(f"Database: {len(drugs)} drugs available")

profile = client.get_drug_profile(selected_drug)

if not profile:
    st.warning(f"⚠️ No safety data found for **{selected_drug}**")
    st.stop()

# ---------- KPI Section with better layout ----------
st.subheader(f"Safety Profile: {selected_drug}")

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.metric(
        "Total Reports",
        f"{profile['TOTAL_EVENTS']:,}",
    )

with col2:
    serious_pct = profile['SERIOUS_RATE_PCT']
    st.metric(
        "Serious Events",
        f"{serious_pct:.1f}%",
    )

with col3:
    fatal_pct = profile['FATAL_RATE_PCT']
    st.metric(
        "Fatal Events",
        f"{fatal_pct:.1f}%",
    )

with col4:
    st.metric(
        "Unique Patients",
        f"{profile['APPROX_UNIQUE_PATIENTS']:,}",
    )

st.divider()

# ---------- Content Tabs with enhanced styling ----------
tab_reactions, tab_demographics = st.tabs([
    "🧬 Adverse Reactions",
    "👥 Patient Demographics"
])

with tab_reactions:
    reactions_df = client.get_top_reactions(selected_drug, 10)
    if reactions_df is not None and len(reactions_df) > 0:
        left, right = st.columns([2, 1], gap="medium")

        with left:
            reactions_sorted = reactions_df.sort_values("REACTION_COUNT")
            fig = px.bar(
                reactions_sorted,
                x="REACTION_COUNT",
                y="REACTION_NAME",
                orientation="h",
                title="Most Common Adverse Reactions",
                color="REACTION_COUNT",
                color_continuous_scale=["#06b6d4", "#0891b2"],
                labels={"REACTION_COUNT": "Reports", "REACTION_NAME": ""}
            )
            fig.update_layout(
                template="plotly_dark",
                height=440,
                showlegend=False,
                margin=dict(l=10, r=10, t=50, b=10),
                xaxis_title="Number of Reports",
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=12),
                hovermode="closest"
            )
            fig.update_traces(hovertemplate="<b>%{y}</b><br>%{x:,} reports<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)

        with right:
            serious = int(reactions_df["SERIOUS_REACTION_COUNT"].sum())
            non_serious = int(reactions_df["REACTION_COUNT"].sum()) - serious
            total = serious + non_serious

            fig = px.pie(
                names=["Serious", "Non-Serious"],
                values=[serious, non_serious],
                title="Event Classification",
                hole=0.55,
                color_discrete_sequence=["#ef4444", "#10b981"]
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
                textposition="inside",
                textinfo="percent"
            )
            fig.update_layout(
                template="plotly_dark",
                height=440,
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=12),
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Detailed Reaction List", expanded=False):
            st.dataframe(
                reactions_df.sort_values("REACTION_COUNT", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "REACTION_NAME": st.column_config.TextColumn("Reaction"),
                    "REACTION_COUNT": st.column_config.NumberColumn("Total Reports"),
                    "SERIOUS_REACTION_COUNT": st.column_config.NumberColumn("Serious Reports")
                }
            )
    else:
        st.info("📭 No reaction data available for this drug.")

with tab_demographics:
    demo = client.get_demographics(selected_drug)
    if demo is not None and len(demo) > 0:
        d1, d2 = st.columns(2, gap="medium")

        with d1:
            by_sex = demo.groupby("PATIENT_SEX", as_index=False)["EVENT_COUNT"].sum()
            fig = px.pie(
                by_sex,
                names="PATIENT_SEX",
                values="EVENT_COUNT",
                title="Events by Patient Sex",
                hole=0.5,
                color_discrete_sequence=["#06b6d4", "#8b5cf6", "#ec4899"]
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
                textposition="inside",
                textinfo="percent"
            )
            fig.update_layout(
                template="plotly_dark",
                height=400,
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=12),
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with d2:
            by_age = demo.groupby("PATIENT_AGE_GROUP", as_index=False)["EVENT_COUNT"].sum()
            fig = px.bar(
                by_age,
                x="PATIENT_AGE_GROUP",
                y="EVENT_COUNT",
                title="Events by Age Group",
                color="EVENT_COUNT",
                color_continuous_scale=["#0891b2", "#06b6d4"],
                labels={"EVENT_COUNT": "Number of Reports", "PATIENT_AGE_GROUP": ""}
            )
            fig.update_layout(
                template="plotly_dark",
                height=400,
                xaxis_title="Age Group",
                yaxis_title="Number of Reports",
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=12),
                hovermode="x unified"
            )
            fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y:,} reports<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("📋 Detailed Demographics", expanded=False):
            st.dataframe(
                demo.sort_values("EVENT_COUNT", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "PATIENT_SEX": st.column_config.TextColumn("Sex"),
                    "PATIENT_AGE_GROUP": st.column_config.TextColumn("Age Group"),
                    "EVENT_COUNT": st.column_config.NumberColumn("Reports")
                }
            )
    else:
        st.info("📭 No demographic data available for this drug.")

st.divider()

# Footer
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    st.caption(
        "**Data Source:** openFDA • **Pipeline:** Raw → Bronze → Silver (deduplicated, 3-year window) → Gold • "
        "**Updates:** Refreshed via dbt"
    )