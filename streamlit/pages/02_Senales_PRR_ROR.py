# PRR/ROR disproportionality signals page (Spanish)
# Co-authored with CoCo
import streamlit as st
import pandas as pd
from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme, note
from components.charts import create_bar_chart
from components.labels import localize_df

st.set_page_config(page_title="Señales PRR/ROR", page_icon="📈", layout="wide")
apply_theme()
render_sidebar()

st.title("📈 Señales de desproporcionalidad (PRR / ROR)")
st.markdown("Detección de señales de seguridad por par medicamento–reacción")

st.info(
    "El **PRR** (Proportional Reporting Ratio) y el **ROR** (Reporting Odds Ratio) "
    "miden si una reacción se reporta **más de lo esperado** para un medicamento. "
    "Una señal se marca cuando **PRR ≥ 2**, **χ² ≥ 4** y al menos **3 reportes**. "
    "*No implican causalidad* — son indicadores para investigar."
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

df = df[df["PRR"].fillna(0) >= min_prr]
if len(df) == 0:
    st.warning(f"No hay señales con PRR ≥ {min_prr}.")
    st.stop()

# KPIs (computed over the full table, not the limited slice)
counts = client.get_signal_counts(drug_filter, min_prr)
crow = counts.iloc[0] if counts is not None and len(counts) > 0 else None
k1, k2, k3 = st.columns(3)
k1.metric("Señales detectadas", f"{int(crow['N']):,}" if crow is not None else "—")
k2.metric("Medicamentos con señal", f"{int(crow['DRUGS']):,}" if crow is not None else "—")
k3.metric("PRR mediano", f"{crow['MED_PRR']:.1f}" if crow is not None else "—")
note("La tabla muestra las 200 señales más fuertes (por IC95% del ROR). El PRR puede llegar a "
     "valores muy altos cuando una reacción es casi exclusiva de un medicamento, pero con pocos "
     "reportes; por eso el ranking usa el IC inferior y aquí se muestra el **PRR mediano**, más representativo.")
st.divider()

# Top signals chart
st.subheader("Señales principales")
top = df.head(15).copy()
top["PAR"] = top["DRUG_NAME"] + " → " + top["REACTION_NAME"]
fig = create_bar_chart(
    top.sort_values("PRR"),
    x="PRR", y="PAR",
    title="Top 15 pares medicamento–reacción (PRR)",
    labels={"PRR": "PRR", "PAR": "Par medicamento–reacción"}
)
st.plotly_chart(fig, use_container_width=True)

# Detail table (is_signal is always true here — the query pre-filters signals — so hide it)
st.subheader("Detalle de señales")
detail = df.drop(columns=[c for c in ["IS_SIGNAL"] if c in df.columns])
st.dataframe(localize_df(detail), use_container_width=True, hide_index=True)

st.divider()
st.caption("PRR/ROR calculados sobre AGG_DISPROPORTIONALITY · cohorte monitoreada · ventana móvil de 3 años · openFDA")