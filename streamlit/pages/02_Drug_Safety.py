import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme
from components.charts import create_bar_chart

st.set_page_config(page_title="Seguridad de Medicamentos", page_icon="⚠️", layout="wide")
render_sidebar()
apply_theme()

st.title("⚠️ Perfiles de Seguridad de Medicamentos")
st.markdown("Análisis detallado de seguridad para medicamentos individuales")

client = SnowflakeClient()
drugs = client.get_drugs()
if not drugs:
    st.error("No hay datos disponibles")
    st.stop()

selected_drugs = st.multiselect(
    "Seleccionar medicamentos para comparar",
    drugs,
    default=[drugs[0]] if drugs else None
)

if selected_drugs:
    st.subheader("Métricas de comparación")
    comparison_data = []
    for drug in selected_drugs:
        profile = client.get_drug_profile(drug)
        if profile:
            comparison_data.append(profile)

    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)

        st.subheader("Comparación de tasa de gravedad")
        fig = create_bar_chart(comparison_df, x="DRUG_NAME", y="SERIOUS_RATE_PCT",
                               title="Tasa de eventos graves por medicamento")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Comparación de tasa de mortalidad")
        fig = create_bar_chart(comparison_df, x="DRUG_NAME", y="FATAL_RATE_PCT",
                               title="Tasa de eventos mortales por medicamento")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Porcentajes calculados a partir de los reportes de eventos adversos")