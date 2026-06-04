import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.charts import create_bar_chart, create_pie_chart

# Page configuration
st.set_page_config(
    page_title="FDA PharmaVigilance",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
render_sidebar()

# Title
st.title("🏥 FDA PharmaVigilance Dashboard")
st.markdown("Real-time adverse event monitoring and pharmaceutical safety analysis")

# Initialize Snowflake client
client = SnowflakeClient()

# Get drugs for selector
drugs = client.get_drugs()

if not drugs:
    st.error("No data available. Please ensure Snowflake is configured correctly.")
    st.stop()

# Select drug
selected_drug = st.selectbox("Select Drug", drugs, key="drug_selector")

# Get drug profile
profile = client.get_drug_profile(selected_drug)

if profile:
    # Key metrics
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric(
        "Total Events",
        f"{profile['TOTAL_EVENTS']:,}",
        help="Total adverse events reported"
    )
    col2.metric(
        "Serious Rate",
        f"{profile['SERIOUS_RATE_PCT']:.1f}%",
        help="Percentage of serious adverse events"
    )
    col3.metric(
        "Fatal Rate",
        f"{profile['FATAL_RATE_PCT']:.1f}%",
        help="Percentage of fatal adverse events"
    )
    col4.metric(
        "Approx. Patients",
        f"{profile['APPROX_UNIQUE_PATIENTS']:,}",
        help="Approximate unique patients affected"
    )
    
    st.markdown("---")
    
    # Top reactions
    st.subheader("Top 10 Reactions")
    reactions_df = client.get_top_reactions(selected_drug, 10)
    
    if reactions_df is not None and len(reactions_df) > 0:
        # Bar chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_bar_chart(
                reactions_df,
                x="REACTION_NAME",
                y="REACTION_COUNT",
                title="Reaction Frequency",
                labels={"REACTION_NAME": "Reaction", "REACTION_COUNT": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Serious vs Non-Serious
        with col2:
            pie_data = pd.DataFrame({
                "Type": ["Serious", "Non-Serious"],
                "Count": [
                    reactions_df["SERIOUS_REACTION_COUNT"].sum(),
                    reactions_df["REACTION_COUNT"].sum() - reactions_df["SERIOUS_REACTION_COUNT"].sum()
                ]
            })
            fig = create_pie_chart(
                pie_data,
                values="Count",
                names="Type",
                title="Serious vs Non-Serious"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Reactions table
        st.subheader("Reactions Detail")
        st.dataframe(reactions_df, use_container_width=True)
    
    # Demographics
    st.markdown("---")
    st.subheader("Patient Demographics")
    
    demographics_df = client.get_demographics(selected_drug)
    if demographics_df is not None and len(demographics_df) > 0:
        st.dataframe(demographics_df, use_container_width=True)
else:
    st.warning(f"No data found for {selected_drug}")

st.markdown("---")
st.markdown("*Dashboard auto-refreshes every 5 minutes. Last update tracked by dbt.*")
