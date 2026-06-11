"""Sidebar component for Streamlit."""
import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown("## 💊 PharmaVigilance")
        st.caption("FDA adverse-event analytics")
        st.divider()

        st.markdown("### Navigation")
        st.markdown(
            "- **Dashboard** — overview & key metrics\n"
            "- **Drug Safety** — individual drug profiles\n"
            "- **Demographics** — patient analysis\n"
            "- **Polypharmacy** — drug-combination signals"
        )
        st.divider()

        st.markdown("### About")
        st.markdown(
            "Adverse-event monitoring & pharmaceutical safety analysis.\n\n"
            "**Source:** openFDA FAERS · rolling 3-year window\n\n"
            "**Refresh:** via dbt pipeline"
        )