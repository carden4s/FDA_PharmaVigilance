import streamlit as st
import pandas as pd

from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme, hero
from components.charts import create_bar_chart, create_pie_chart

st.set_page_config(page_title="FarmacoVigilancia FDA", page_icon="💊",
                   layout="wide", initial_sidebar_state="expanded")
apply_theme()
render_sidebar()

hero("🏥 Panel de FarmacoVigilancia FDA",
     "Monitoreo de eventos adversos y análisis de seguridad farmacéutica · openFDA")

client = SnowflakeClient()
drugs = client.get_drugs()
if not drugs:
    st.error("No hay datos disponibles. Verifique la conexión a Snowflake y que existan las tablas gold en FARMACEUTICADATA.FDA_EXPERIENCE.")
    st.stop()

selected_drug = st.selectbox("Seleccionar medicamento", drugs)
profile = client.get_drug_profile(selected_drug)
if not profile:
    st.warning(f"No se encontraron datos para {selected_drug}")
    st.stop()

st.subheader(f"📊 {selected_drug} — Resumen de seguridad")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Eventos totales", f"{profile['TOTAL_EVENTS']:,}")
c2.metric("Tasa de gravedad", f"{profile['SERIOUS_RATE_PCT']:.1f}%")
c3.metric("Tasa de mortalidad", f"{profile['FATAL_RATE_PCT']:.1f}%")
c4.metric("Pacientes aprox.", f"{profile['APPROX_UNIQUE_PATIENTS']:,}")

st.divider()
tab_react, tab_demo, tab_poly = st.tabs(["🧬 Reacciones", "👥 Demografía", "⚗️ Polifarmacia"])

with tab_react:
    rdf = client.get_top_reactions(selected_drug, 10)
    if rdf is not None and len(rdf) > 0:
        left, right = st.columns([2, 1])
        with left:
            st.plotly_chart(
                create_bar_chart(rdf.sort_values("REACTION_COUNT"),
                                 x="REACTION_COUNT", y="REACTION_NAME",
                                 title="10 reacciones principales"),
                use_container_width=True)
        with right:
            serious = int(rdf["SERIOUS_REACTION_COUNT"].sum())
            non = int(rdf["REACTION_COUNT"].sum()) - serious
            pie = pd.DataFrame({"Tipo": ["Graves", "No graves"], "Cantidad": [serious, non]})
            st.plotly_chart(create_pie_chart(pie, values="Cantidad", names="Tipo",
                                             title="Graves vs No graves"),
                            use_container_width=True)
        st.markdown("##### Detalle de reacciones")
        st.dataframe(rdf, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de reacciones para este medicamento.")

with tab_demo:
    ddf = client.get_demographics(selected_drug)
    if ddf is not None and len(ddf) > 0:
        st.dataframe(ddf, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos demográficos para este medicamento.")

with tab_poly:
    st.caption("Combinaciones de medicamentos reportadas junto a otros fármacos (señales de interacción).")
    pdf = client.get_polypharmacy_signals(limit=200)
    if pdf is not None and len(pdf) > 0:
        # combinations involving the selected drug
        mask = (pdf["DRUG_1_NAME"] == selected_drug) | (pdf["DRUG_2_NAME"] == selected_drug)
        sub = pdf[mask].copy()
        if len(sub) == 0:
            st.info(f"No hay combinaciones registradas para {selected_drug}. Mostrando las principales globales.")
            sub = pdf.copy()
        sub["PAR"] = sub["DRUG_1_NAME"] + " + " + sub["DRUG_2_NAME"]
        top = sub.sort_values("CO_OCCURRENCE_COUNT", ascending=False).head(12)
        st.plotly_chart(
            create_bar_chart(top.sort_values("CO_OCCURRENCE_COUNT"),
                             x="CO_OCCURRENCE_COUNT", y="PAR",
                             title="Principales combinaciones por coocurrencia"),
            use_container_width=True)
        st.markdown("##### Detalle de combinaciones")
        st.dataframe(
            sub[["DRUG_1_NAME", "DRUG_2_NAME", "CO_OCCURRENCE_COUNT", "COMBINED_SERIOUS_RATE_PCT"]]
               .rename(columns={
                   "DRUG_1_NAME": "Medicamento 1", "DRUG_2_NAME": "Medicamento 2",
                   "CO_OCCURRENCE_COUNT": "Coocurrencias", "COMBINED_SERIOUS_RATE_PCT": "Tasa gravedad (%)"})
               .sort_values("Coocurrencias", ascending=False),
            use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de polifarmacia disponibles.")

st.divider()
st.caption("Datos: openFDA · Bronze → Silver (deduplicado, 3 años) → Gold · actualizado por dbt")