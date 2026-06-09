import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.charts import create_bar_chart, create_scatter_chart
from components.theme import apply_theme

st.set_page_config(page_title="Polypharmacy Signals", page_icon="⚗️", layout="wide")
apply_theme()
render_sidebar()

st.title("⚗️ Polypharmacy Signals")
st.markdown("Analysis of drug combination adverse events")

st.info("""
Polypharmacy signals indicate potential drug-drug interaction risks.
These are adverse events where multiple drugs were reported together in the same report.
""")

client = SnowflakeClient()

# Get polypharmacy signals
polypharmacy_df = client.get_polypharmacy_signals(limit=50)

if polypharmacy_df is not None and len(polypharmacy_df) > 0:
    # Summary
    st.subheader("Drug Combination Summary")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Unique Combinations", len(polypharmacy_df))
    col2.metric("Total Co-occurrences", polypharmacy_df["CO_OCCURRENCE_COUNT"].sum())
    col3.metric("Avg Serious Rate", f"{polypharmacy_df['COMBINED_SERIOUS_RATE_PCT'].mean():.1f}%")
    
    st.markdown("---")
    
    # Top combinations
    st.subheader("Top Drug Combinations")
    top_combinations = polypharmacy_df.head(10)
    
    fig = create_bar_chart(
        top_combinations,
        x="DRUG_1_NAME",
        y="CO_OCCURRENCE_COUNT",
        title="Top 10 Drug Combinations by Co-occurrence Count"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Scatter plot: Co-occurrence vs Serious Rate
    st.subheader("Co-occurrence vs Serious Rate")
    fig = create_scatter_chart(
        polypharmacy_df,
        x="CO_OCCURRENCE_COUNT",
        y="COMBINED_SERIOUS_RATE_PCT",
        title="Drug Combinations: Frequency vs Serious Rate",
        labels={"CO_OCCURRENCE_COUNT": "Co-occurrence Count", "COMBINED_SERIOUS_RATE_PCT": "Serious Rate (%)"}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Table
    st.subheader("All Drug Combinations")
    st.dataframe(polypharmacy_df, use_container_width=True)
else:
    st.warning("No polypharmacy data available")

st.markdown("---")
st.markdown("*Polypharmacy signals help identify potential drug-drug interactions*")
