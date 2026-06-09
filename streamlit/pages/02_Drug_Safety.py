import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.charts import create_bar_chart, create_line_chart
from components.theme import apply_theme

st.set_page_config(page_title="Drug Safety", page_icon="⚠️", layout="wide")
apply_theme()
render_sidebar()

st.title("⚠️ Drug Safety Profiles")
st.markdown("Detailed safety analysis for individual drugs")

client = SnowflakeClient()
drugs = client.get_drugs()

if not drugs:
    st.error("No data available")
    st.stop()

# Multi-select for comparison
selected_drugs = st.multiselect(
    "Select Drugs for Comparison",
    drugs,
    default=[drugs[0]] if drugs else None
)

if selected_drugs:
    # Compare drugs
    st.subheader("Comparison Metrics")
    
    comparison_data = []
    for drug in selected_drugs:
        profile = client.get_drug_profile(drug)
        if profile:
            comparison_data.append(profile)
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Serious rate comparison
        st.subheader("Serious Rate Comparison")
        fig = create_bar_chart(
            comparison_df,
            x="DRUG_NAME",
            y="SERIOUS_RATE_PCT",
            title="Serious Event Rate by Drug"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Fatal rate comparison
        st.subheader("Fatal Rate Comparison")
        fig = create_bar_chart(
            comparison_df,
            x="DRUG_NAME",
            y="FATAL_RATE_PCT",
            title="Fatal Event Rate by Drug"
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("*Percentages calculated from adverse event reports*")
