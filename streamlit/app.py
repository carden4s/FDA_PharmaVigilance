import streamlit as st
import pandas as pd

from data.snowflake_client import SnowflakeClient
from components.sidebar import render_sidebar
from components.theme import apply_theme, hero
from components.charts import create_bar_chart, create_pie_chart

st.set_page_config(page_title="FDA PharmaVigilance", page_icon="💊",
                   layout="wide", initial_sidebar_state="expanded")
apply_theme()
render_sidebar()

hero("🏥 FDA PharmaVigilance Dashboard",
     "Adverse-event monitoring & pharmaceutical safety analysis · openFDA")

client = SnowflakeClient()
drugs = client.get_drugs()
if not drugs:
    st.error("No data available. Check Snowflake connection and that gold tables exist in FARMACEUTICADATA.FDA_EXPERIENCE.")
    st.stop()

selected_drug = st.selectbox("Select drug", drugs)
profile = client.get_drug_profile(selected_drug)
if not profile:
    st.warning(f"No data found for {selected_drug}")
    st.stop()

st.subheader(f"📊 {selected_drug} — Safety Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Events", f"{profile['TOTAL_EVENTS']:,}")
c2.metric("Serious Rate", f"{profile['SERIOUS_RATE_PCT']:.1f}%")
c3.metric("Fatal Rate", f"{profile['FATAL_RATE_PCT']:.1f}%")
c4.metric("Approx. Patients", f"{profile['APPROX_UNIQUE_PATIENTS']:,}")

st.divider()
tab_react, tab_demo = st.tabs(["🧬 Reactions", "👥 Demographics"])

with tab_react:
    rdf = client.get_top_reactions(selected_drug, 10)
    if rdf is not None and len(rdf) > 0:
        left, right = st.columns([2, 1])
        with left:
            st.plotly_chart(
                create_bar_chart(rdf.sort_values("REACTION_COUNT"),
                                 x="REACTION_COUNT", y="REACTION_NAME",
                                 title="Top 10 Reactions"),
                use_container_width=True)
        with right:
            serious = int(rdf["SERIOUS_REACTION_COUNT"].sum())
            non = int(rdf["REACTION_COUNT"].sum()) - serious
            pie = pd.DataFrame({"Type": ["Serious", "Non-Serious"], "Count": [serious, non]})
            st.plotly_chart(create_pie_chart(pie, values="Count", names="Type",
                                             title="Serious vs Non-Serious"),
                            use_container_width=True)
        st.markdown("##### Reaction detail")
        st.dataframe(rdf, use_container_width=True, hide_index=True)
    else:
        st.info("No reaction data for this drug.")

with tab_demo:
    ddf = client.get_demographics(selected_drug)
    if ddf is not None and len(ddf) > 0:
        st.dataframe(ddf, use_container_width=True, hide_index=True)
    else:
        st.info("No demographic data for this drug.")

st.divider()
st.caption("Data: openFDA · Bronze → Silver (dedup, 3-yr) → Gold · refreshed by dbt")