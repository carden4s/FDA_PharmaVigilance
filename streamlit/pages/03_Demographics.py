import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.charts import create_bar_chart, create_pie_chart

st.set_page_config(page_title="Demographics", page_icon="👥", layout="wide")
render_sidebar()

st.title("👥 Patient Demographics")
st.markdown("Adverse event analysis by patient characteristics")

client = SnowflakeClient()
drugs = client.get_drugs()

if not drugs:
    st.error("No data available")
    st.stop()

selected_drug = st.selectbox("Select Drug", drugs)

if selected_drug:
    demographics_df = client.get_demographics(selected_drug)
    
    if demographics_df is not None and len(demographics_df) > 0:
        st.subheader(f"Demographics for {selected_drug}")
        
        # Age distribution
        age_data = demographics_df.groupby("PATIENT_AGE_GROUP").agg({
            "PATIENT_COUNT": "sum",
            "SERIOUS_RATE_PCT": "mean"
        }).reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_bar_chart(
                age_data,
                x="PATIENT_AGE_GROUP",
                y="PATIENT_COUNT",
                title="Patients by Age Group"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = create_bar_chart(
                age_data,
                x="PATIENT_AGE_GROUP",
                y="SERIOUS_RATE_PCT",
                title="Serious Rate by Age Group"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Sex distribution
        st.subheader("Gender Distribution")
        sex_data = demographics_df.groupby("PATIENT_SEX").agg({
            "PATIENT_COUNT": "sum"
        }).reset_index()
        
        fig = create_pie_chart(
            sex_data,
            values="PATIENT_COUNT",
            names="PATIENT_SEX",
            title="Patients by Gender"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Full table
        st.subheader("Detailed Demographics")
        st.dataframe(demographics_df, use_container_width=True)

st.markdown("---")
st.markdown("*Data based on adverse event reports in FAERS database*")
