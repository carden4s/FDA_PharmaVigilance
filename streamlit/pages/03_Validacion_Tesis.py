# Thesis validation page: forest plot + positive controls (Spanish)
# Co-authored with CoCo
import streamlit as st
import pandas as pd

from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme, note
from components.charts import create_forest_plot
from components.labels import localize_df

st.set_page_config(page_title="Validación (Tesis)", page_icon="🔬", layout="wide")
apply_theme()
render_sidebar()

st.title("🔬 Validación del método (figuras de tesis)")
st.markdown("Evidencia de validez del método de desproporcionalidad para el capítulo de resultados.")

client = SnowflakeClient()

# Positive-control validation (face validity)
st.subheader("1. Validación con controles positivos")
st.caption("Asociaciones fármaco–reacción documentadas por la FDA. Si el método es válido, "
           "deben detectarse como señales (validez aparente).")

pc = client.get_positive_controls()
if pc is not None and len(pc) > 0:
    detected = int(pc["DETECTED"].sum())
    total = len(pc)
    c1, c2 = st.columns(2)
    c1.metric("Controles detectados", f"{detected} / {total}")
    c2.metric("Sensibilidad aparente", f"{100.0 * detected / total:.0f}%")
    st.dataframe(localize_df(pc), use_container_width=True, hide_index=True)
    note("Un control no detectado no implica fallo del método: puede reflejar dilución por clase "
         "(p. ej. una estatina cuyo efecto se atenúa porque el comparador contiene otras estatinas). "
         "Ver docs/LIMITATIONS.md §6.")
else:
    st.info("No hay datos de controles positivos. Ejecute `dbt build` de `val_positive_controls`.")

st.divider()

# Forest plot of top signals (PRR / ROR with 95% CI)
st.subheader("2. Gráfico de bosque (forest plot) — señales principales")
st.caption("Estimación puntual e intervalo de confianza del 95% por par fármaco–reacción.")

cf1, cf2 = st.columns([1, 2])
with cf1:
    metric = st.radio("Medida", ["ROR", "PRR"], horizontal=True)
with cf2:
    topn = st.slider("Número de señales", 5, 30, 15)

sig = client.get_signals_for_plot(topn)
if sig is not None and len(sig) > 0:
    sig = sig.copy()
    sig["PAR"] = sig["DRUG_NAME"] + " → " + sig["REACTION_NAME"]
    if metric == "ROR":
        point, lo, hi = "ROR", "ROR_LOWER_95", "ROR_UPPER_95"
    else:
        point, lo, hi = "PRR", "PRR_LOWER_95", "PRR_UPPER_95"
    sig = sig.sort_values(point)
    st.plotly_chart(
        create_forest_plot(sig, point, lo, hi, "PAR",
                           f"{metric} con IC 95% — top {topn} señales"),
        use_container_width=True)
    note("Línea de referencia en 1: valores a la derecha indican reporte desproporcionado. "
         "Un intervalo de confianza que no cruza 1 respalda la señal. Escala logarítmica.")
else:
    st.info("No hay señales disponibles. Ejecute `dbt build` de `agg_disproportionality`.")

st.divider()
st.caption("Datos: AGG_DISPROPORTIONALITY y VAL_POSITIVE_CONTROLS · openFDA · ventana móvil 3 años")