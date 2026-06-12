import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme
from components.charts import create_bar_chart

st.set_page_config(page_title="Señales PRR/ROR", page_icon="📈", layout="wide")
render_sidebar()
apply_theme()

st.title("📈 Señales de Desproporcionalidad (PRR / ROR)")
st.markdown("Detección de señales de seguridad por par medicamento–reacción")

st.info(
    "El **PRR** (Proportional Reporting Ratio) y el **ROR** (Reporting Odds Ratio) "
    "miden si una reacción se reporta **más de lo esperado** para un medicamento. "
    "Una señal suele considerarse relevante cuando **PRR ≥ 2**, con al menos **3 reportes** "
    "y respaldo estadístico. *No implican causalidad* — son indicadores para investigar."
)

client = SnowflakeClient()
drugs = client.get_drugs()
if not drugs:
    st.error("No hay datos disponibles. Verifique la conexión a Snowflake.")
    st.stop()

col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    options = ["(Todos los medicamentos)"] + drugs
    selected = st.selectbox("Filtrar por medicamento", options)
with col_f2:
    min_prr = st.slider("PRR mínimo", 0.0, 10.0, 2.0, 0.5)

drug_filter = None if selected.startswith("(Todos") else selected
df = client.get_disproportionality(drug_name=drug_filter, limit=200)

if df is None or len(df) == 0:
    st.warning("No hay señales disponibles.")
    st.stop()

# Apply PRR threshold
df = df[df["PRR"].fillna(0) >= min_prr]
if len(df) == 0:
    st.warning(f"No hay señales con PRR ≥ {min_prr}.")
    st.stop()

# KPIs
k1, k2, k3 = st.columns(3)
k1.metric("Pares analizados", f"{len(df):,}")
k2.metric("Señales (PRR ≥ 2)", f"{int((df['PRR'] >= 2).sum()):,}")
k3.metric("PRR máximo", f"{df['PRR'].max():.1f}")

st.divider()

# Top signals chart
st.subheader("Señales principales por PRR")
top = df.head(15).copy()
top["PAR"] = top["DRUG_NAME"] + " → " + top["REACTION_NAME"]
fig = create_bar_chart(
    top.sort_values("PRR"),
    x="PRR", y="PAR",
    title="Top 15 pares medicamento–reacción (PRR)"
)
st.plotly_chart(fig, use_container_width=True)

# Detail table
st.subheader("Detalle de señales")
show = df.rename(columns={
    "DRUG_NAME": "Medicamento",
    "REACTION_NAME": "Reacción",
    "REPORTS_WITH_BOTH": "Reportes (ambos)",
    "N_DRUG": "Reportes del medicamento",
    "N_REACTION": "Reportes de la reacción",
    "PRR": "PRR",
    "ROR": "ROR",
})
st.dataframe(show, use_container_width=True, hide_index=True)

st.divider()
st.caption("PRR/ROR calculados sobre la tabla AGG_DISPROPORTIONALITY · ventana móvil de 3 años · openFDA")