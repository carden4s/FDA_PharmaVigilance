import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme
from components.charts import create_bar_chart, create_pie_chart

st.set_page_config(page_title="Demografía", page_icon="👥", layout="wide")
render_sidebar()
apply_theme()

st.title("👥 Demografía de Pacientes")
st.markdown("Análisis de eventos adversos por características del paciente")

client = SnowflakeClient()
drugs = client.get_drugs()
if not drugs:
    st.error("No hay datos disponibles")
    st.stop()

selected_drug = st.selectbox("Seleccionar medicamento", drugs)

if selected_drug:
    demographics_df = client.get_demographics(selected_drug)
    if demographics_df is not None and len(demographics_df) > 0:
        st.subheader(f"Demografía de {selected_drug}")

        age_data = demographics_df.groupby("PATIENT_AGE_GROUP").agg({
            "PATIENT_COUNT": "sum",
            "SERIOUS_RATE_PCT": "mean"
        }).reset_index()

        col1, col2 = st.columns(2)
        with col1:
            fig = create_bar_chart(age_data, x="PATIENT_AGE_GROUP", y="PATIENT_COUNT",
                                   title="Pacientes por grupo de edad")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = create_bar_chart(age_data, x="PATIENT_AGE_GROUP", y="SERIOUS_RATE_PCT",
                                   title="Tasa de gravedad por grupo de edad")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Distribución por sexo")
        sex_data = demographics_df.groupby("PATIENT_SEX").agg({"PATIENT_COUNT": "sum"}).reset_index()
        fig = create_pie_chart(sex_data, values="PATIENT_COUNT", names="PATIENT_SEX",
                               title="Pacientes por sexo")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Demografía detallada")
        st.dataframe(demographics_df, use_container_width=True)

st.divider()
st.caption("Datos basados en reportes de eventos adversos de la base FAERS")