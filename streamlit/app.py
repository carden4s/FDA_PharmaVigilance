import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from data.snowflake_client import SnowflakeClient

# ---------- Page config ----------
st.set_page_config(
    page_title="FDA PharmaVigilance",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Enhanced styling with improved colors and contrast ----------
st.markdown("""
<style>
    /* Root palette: medical blue + vibrant accents for clarity */
    :root {
        --bg-primary: #0d1520;
        --bg-secondary: #141d2e;
        --bg-tertiary: #1a2642;
        --accent-primary: #3b82f6;
        --accent-secondary: #60a5fa;
        --danger: #ef4444;
        --success: #10b981;
        --warning: #f59e0b;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --border: #334155;
    }

    * {
        margin: 0;
        padding: 0;
    }

    .main {
        background: linear-gradient(135deg, #0d1520 0%, #141d2e 100%);
        color: var(--text-primary);
    }

    .block-container {
        padding-top: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Hero section - clean and bold */
    .hero {
        background: linear-gradient(135deg, #1a2642 0%, #243451 100%);
        border: 2px solid var(--accent-primary);
        border-radius: 16px;
        padding: 40px;
        margin-bottom: 2.5rem;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.1);
    }

    .hero h1 {
        font-size: 2.8rem;
        font-weight: 800;
        color: var(--text-primary);
        margin: 0 0 0.75rem 0;
        letter-spacing: -0.025em;
    }

    .hero p {
        color: var(--text-secondary);
        font-size: 1rem;
        margin: 0;
        font-weight: 500;
        line-height: 1.5;
    }

    /* Metrics section - vibrant and readable */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2642 0%, #243451 100%);
        border: 1.5px solid var(--border);
        border-radius: 12px;
        padding: 28px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    div[data-testid="stMetric"]:hover {
        border-color: var(--accent-primary);
        box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
        transform: translateY(-3px);
    }

    div[data-testid="stMetric"] label {
        color: var(--text-secondary) !important;
        font-weight: 700;
        font-size: 0.80rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    div[data-testid="stMetricValue"] {
        color: var(--accent-primary) !important;
        font-weight: 800;
        font-size: 2.2rem !important;
    }

    /* Typography hierarchy */
    h1 { color: var(--text-primary); font-weight: 800; margin-top: 1.5rem !important; }
    h2 { color: var(--text-primary); font-weight: 800; margin-top: 1.2rem !important; }
    h3 { color: var(--text-secondary); font-weight: 700; margin-top: 1rem !important; }

    /* Subheader styling */
    [data-testid="stSubheader"] {
        border-bottom: 3px solid var(--accent-primary);
        padding-bottom: 1rem !important;
        font-size: 1.5rem !important;
        letter-spacing: -0.015em;
        color: var(--text-primary) !important;
    }

    /* Divider enhancement */
    hr {
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        border: none;
        height: 2px;
        margin: 2.5rem 0 !important;
    }

    /* Tab styling */
    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--accent-primary) !important;
        border-bottom: 3px solid var(--accent-primary) !important;
    }

    [data-testid="stTabs"] button {
        color: var(--text-secondary);
        transition: all 0.2s ease;
    }

    [data-testid="stTabs"] button:hover {
        color: var(--text-primary);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141d2e 0%, #1a2642 100%);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        border-bottom: 3px solid var(--accent-primary);
        padding-bottom: 0.8rem;
        color: var(--text-primary);
    }

    /* Selectbox styling */
    [data-testid="stSelectbox"] > div:first-child {
        border-color: var(--border) !important;
        background-color: rgba(20, 29, 46, 0.6) !important;
    }

    [data-testid="stSelectbox"] > div:first-child:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }

    [data-testid="stSelectbox"] label {
        color: var(--text-secondary) !important;
        font-weight: 600;
    }

    /* Data table styling */
    [data-testid="stDataFrame"] {
        background: var(--bg-secondary) !important;
    }

    [data-testid="stDataFrame"] table {
        font-size: 0.9rem;
        color: var(--text-primary);
    }

    [data-testid="stDataFrame"] tbody td {
        color: var(--text-primary);
    }

    [data-testid="stDataFrame"] thead th {
        color: var(--text-primary);
        background-color: rgba(59, 130, 246, 0.1);
        border-bottom: 2px solid var(--accent-primary);
    }

    /* Caption styling */
    [data-testid="stCaption"] {
        color: var(--text-secondary);
        font-size: 0.85rem;
        line-height: 1.5;
    }

    /* Info/warning boxes */
    [data-testid="stInfo"] {
        border-radius: 12px;
        border-left: 4px solid var(--accent-primary);
        background-color: rgba(59, 130, 246, 0.08);
        color: var(--text-primary);
    }

    [data-testid="stWarning"] {
        border-radius: 12px;
        border-left: 4px solid var(--warning);
        background-color: rgba(245, 158, 11, 0.08);
        color: var(--text-primary);
    }

    [data-testid="stError"] {
        border-radius: 12px;
        border-left: 4px solid var(--danger);
        background-color: rgba(239, 68, 68, 0.08);
        color: var(--text-primary);
    }

    /* Expander styling */
    [data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: 8px;
        background-color: rgba(26, 38, 66, 0.5);
    }

    [data-testid="stExpander"] details summary {
        color: var(--text-primary);
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero {
            padding: 28px 20px;
        }

        .hero h1 {
            font-size: 2rem;
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
  <h1>💊 FDA PharmaVigilance Dashboard</h1>
  <p>Real-time adverse event monitoring for pharmaceutical safety • openFDA data • 3-year rolling analysis</p>
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
    selected_drug = st.selectbox("Select drug to analyze", sorted(drugs), help="Choose a pharmaceutical drug to view safety data")
    st.caption(f"📊 Database contains {len(drugs)} drugs")

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
tab_reactions, tab_demographics, tab_trends, tab_outcomes = st.tabs([
    "🧬 Adverse Reactions",
    "👥 Patient Demographics",
    "📈 Trends & Patterns",
    "🎯 Outcome Analysis"
])

# ===== TAB 1: Reactions =====
with tab_reactions:
    reactions_df = client.get_top_reactions(selected_drug, 10)
    if reactions_df is not None and len(reactions_df) > 0:
        col1, col2 = st.columns([2, 1], gap="large")

        with col1:
            reactions_sorted = reactions_df.sort_values("REACTION_COUNT")
            fig = px.bar(
                reactions_sorted,
                x="REACTION_COUNT",
                y="REACTION_NAME",
                orientation="h",
                title="Top 10 Adverse Reactions",
                color="REACTION_COUNT",
                color_continuous_scale=["#60a5fa", "#3b82f6", "#1d4ed8"],
                labels={"REACTION_COUNT": "Reports", "REACTION_NAME": ""}
            )
            fig.update_layout(
                template="plotly_dark",
                height=480,
                showlegend=False,
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis_title="Number of Reports",
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0.2)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=13, color="var(--text-primary)"),
                hovermode="closest",
                xaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)"),
            )
            fig.update_traces(
                hovertemplate="<b>%{y}</b><br>📊 %{x:,} reports<extra></extra>",
                marker=dict(line=dict(width=1, color="rgba(59, 130, 246, 0.5)"))
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            serious = int(reactions_df["SERIOUS_REACTION_COUNT"].sum())
            non_serious = int(reactions_df["REACTION_COUNT"].sum()) - serious

            fig = px.pie(
                names=["Serious", "Non-Serious"],
                values=[serious, non_serious],
                title="Severity Distribution",
                hole=0.6,
                color_discrete_sequence=["#ef4444", "#10b981"]
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>%{value:,} reports (%{percent})<extra></extra>",
                textposition="inside",
                textinfo="label+percent",
                textfont=dict(size=12, color="white"),
                marker=dict(line=dict(width=2, color="rgba(13, 21, 32, 0.8)"))
            )
            fig.update_layout(
                template="plotly_dark",
                height=480,
                margin=dict(l=10, r=10, t=60, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=12),
                showlegend=True,
                legend=dict(orientation="v", yanchor="bottom", y=0, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        with st.expander("📋 Detailed Reaction List", expanded=False):
            st.dataframe(
                reactions_df.sort_values("REACTION_COUNT", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "REACTION_NAME": st.column_config.TextColumn("Reaction Type", width="large"),
                    "REACTION_COUNT": st.column_config.NumberColumn("Total Reports", format="%d"),
                    "SERIOUS_REACTION_COUNT": st.column_config.NumberColumn("Serious Reports", format="%d")
                }
            )
    else:
        st.info("📭 No reaction data available for this drug.")

# ===== TAB 2: Demographics =====
with tab_demographics:
    demo = client.get_demographics(selected_drug)
    if demo is not None and len(demo) > 0:
        d1, d2 = st.columns(2, gap="large")

        with d1:
            by_sex = demo.groupby("PATIENT_SEX", as_index=False)["EVENT_COUNT"].sum().sort_values("EVENT_COUNT", ascending=False)
            fig = px.pie(
                by_sex,
                names="PATIENT_SEX",
                values="EVENT_COUNT",
                title="Events by Patient Sex",
                hole=0.55,
                color_discrete_sequence=["#3b82f6", "#8b5cf6", "#ec4899", "#f97316"]
            )
            fig.update_traces(
                hovertemplate="<b>%{label}</b><br>%{value:,} reports (%{percent})<extra></extra>",
                textposition="inside",
                textinfo="label+percent",
                textfont=dict(size=12, color="white"),
                marker=dict(line=dict(width=2, color="rgba(13, 21, 32, 0.8)"))
            )
            fig.update_layout(
                template="plotly_dark",
                height=420,
                margin=dict(l=10, r=10, t=60, b=10),
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
                color_continuous_scale=["#93c5fd", "#3b82f6", "#1e40af"],
                labels={"EVENT_COUNT": "Reports", "PATIENT_AGE_GROUP": "Age Group"}
            )
            fig.update_layout(
                template="plotly_dark",
                height=420,
                xaxis_title="Age Group",
                yaxis_title="Number of Reports",
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=60, b=20),
                plot_bgcolor="rgba(0,0,0,0.2)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="system-ui, sans-serif", size=12),
                hovermode="x unified",
                xaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)"),
            )
            fig.update_traces(
                hovertemplate="<b>%{x}</b><br>📊 %{y:,} reports<extra></extra>",
                marker=dict(line=dict(width=1, color="rgba(59, 130, 246, 0.5)"))
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        with st.expander("📋 Detailed Demographics", expanded=False):
            st.dataframe(
                demo.sort_values("EVENT_COUNT", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "PATIENT_SEX": st.column_config.TextColumn("Sex", width="small"),
                    "PATIENT_AGE_GROUP": st.column_config.TextColumn("Age Group", width="medium"),
                    "EVENT_COUNT": st.column_config.NumberColumn("Reports", format="%d")
                }
            )
    else:
        st.info("📭 No demographic data available for this drug.")

# ===== TAB 3: Trends & Patterns =====
with tab_trends:
    st.subheader("Safety Monitoring Timeline")
    
    col_t1, col_t2 = st.columns(2, gap="large")
    
    with col_t1:
        # Mock trend data (in production, get from database)
        months = pd.date_range(end=datetime.now(), periods=24, freq='M')
        trend_data = pd.DataFrame({
            'Month': months,
            'Reports': [100 + i*15 + (i % 5)*20 for i in range(24)]
        })
        
        fig = px.line(
            trend_data,
            x='Month',
            y='Reports',
            title='Reports Over Time (Last 24 Months)',
            markers=True,
            line_shape='smooth'
        )
        fig.update_traces(
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=6, color='#60a5fa', line=dict(width=2, color='#1d4ed8')),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)',
            hovertemplate="<b>%{x|%B %Y}</b><br>📊 %{y} reports<extra></extra>"
        )
        fig.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            plot_bgcolor="rgba(0,0,0,0.2)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="system-ui, sans-serif", size=12),
            xaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)"),
            yaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)", title="Number of Reports"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_t2:
        # Serious events trend
        serious_trend = pd.DataFrame({
            'Month': months,
            'Serious': [20 + i*3 + (i % 4)*5 for i in range(24)],
            'Fatal': [2 + i*0.3 for i in range(24)]
        })
        
        fig = px.area(
            serious_trend,
            x='Month',
            y=['Serious', 'Fatal'],
            title='Serious & Fatal Events Trend',
            color_discrete_map={'Serious': '#f59e0b', 'Fatal': '#ef4444'}
        )
        fig.update_traces(
            line=dict(width=2),
            hovertemplate="<b>%{x|%B %Y}</b><br>%{y:,} events<extra></extra>"
        )
        fig.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            plot_bgcolor="rgba(0,0,0,0.2)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="system-ui, sans-serif", size=12),
            xaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)"),
            yaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)", title="Number of Events"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

# ===== TAB 4: Outcome Analysis =====
with tab_outcomes:
    st.subheader("Patient Outcome Distribution")
    
    col_o1, col_o2 = st.columns(2, gap="large")
    
    with col_o1:
        # Mock outcome data
        outcomes = pd.DataFrame({
            'Outcome': ['Recovered', 'Recovering', 'Not Recovered', 'Fatal', 'Unknown'],
            'Count': [450, 320, 180, 45, 105]
        }).sort_values('Count', ascending=True)
        
        fig = px.barh(
            outcomes,
            x='Count',
            y='Outcome',
            title='Patient Outcomes',
            color='Count',
            color_continuous_scale=['#ef4444', '#f97316', '#f59e0b', '#eab308', '#10b981']
        )
        fig.update_layout(
            template="plotly_dark",
            height=380,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20),
            plot_bgcolor="rgba(0,0,0,0.2)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="system-ui, sans-serif", size=12),
            xaxis_title="Number of Reports",
            yaxis_title="",
            xaxis=dict(gridcolor="rgba(59, 130, 246, 0.1)"),
            hovermode="closest"
        )
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>📊 %{x} reports<extra></extra>",
            marker=dict(line=dict(width=1, color="rgba(59, 130, 246, 0.5)"))
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_o2:
        outcome_pct = outcomes.copy()
        outcome_pct['Percentage'] = (outcome_pct['Count'] / outcome_pct['Count'].sum() * 100).round(1)
        
        fig = px.pie(
            outcome_pct,
            names='Outcome',
            values='Count',
            title='Outcome Percentage Distribution',
            color_discrete_sequence=['#10b981', '#eab308', '#f59e0b', '#f97316', '#ef4444']
        )
        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>%{value} reports (%{percent})<extra></extra>",
            textposition="inside",
            textinfo="label+percent",
            textfont=dict(size=11, color="white"),
            marker=dict(line=dict(width=2, color="rgba(13, 21, 32, 0.8)"))
        )
        fig.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=10, r=10, t=60, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="system-ui, sans-serif", size=12),
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# Footer
st.markdown("""
---
**📊 Data Source:** openFDA • **🔄 Pipeline:** Raw data → Bronze → Silver (deduplicated, 3-year window) → Gold • **⚡ Updates:** Refreshed via dbt

*Last updated: Dynamic · For medical professionals and regulatory analysts*
""")