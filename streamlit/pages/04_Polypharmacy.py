import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme
from components.charts import create_bar_chart, create_scatter_chart

st.set_page_config(page_title="Señales de Polifarmacia", page_icon="⚗️", layout="wide")
render_sidebar()
apply_theme()

st.title("⚗️ Señales de Polifarmacia")
st.markdown("Análisis de eventos adversos por combinaciones de medicamentos")

st.info(
    "Las señales de polifarmacia indican posibles riesgos de interacción entre medicamentos. "
    "Son eventos adversos donde se reportaron varios medicamentos juntos en el mismo reporte."
)

client = SnowflakeClient()
polypharmacy_df = client.get_polypharmacy_signals(limit=50)

if polypharmacy_df is not None and len(polypharmacy_df) > 0:
    st.subheader("Resumen de combinaciones de medicamentos")
    col1, col2, col3 = st.columns(3)
    col1.metric("Combinaciones únicas", len(polypharmacy_df))
    col2.metric("Coocurrencias totales", f"{polypharmacy_df['CO_OCCURRENCE_COUNT'].sum():,}")
    col3.metric("Tasa de gravedad prom.", f"{polypharmacy_df['COMBINED_SERIOUS_RATE_PCT'].mean():.1f}%")

    st.divider()
    st.subheader("Principales combinaciones de medicamentos")
    top_combinations = polypharmacy_df.head(10)
    fig = create_bar_chart(top_combinations, x="DRUG_1_NAME", y="CO_OCCURRENCE_COUNT",
                           title="10 principales combinaciones por coocurrencia")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Coocurrencia vs tasa de gravedad")
    fig = create_scatter_chart(
        polypharmacy_df, x="CO_OCCURRENCE_COUNT", y="COMBINED_SERIOUS_RATE_PCT",
        title="Combinaciones: frecuencia vs gravedad",
        labels={"CO_OCCURRENCE_COUNT": "Coocurrencias", "COMBINED_SERIOUS_RATE_PCT": "Tasa de gravedad (%)"}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Todas las combinaciones de medicamentos")
    st.dataframe(polypharmacy_df, use_container_width=True)
else:
    st.warning("No hay datos de polifarmacia disponibles")

st.divider()
st.caption("Las señales de polifarmacia ayudan a identificar posibles interacciones entre medicamentos")
