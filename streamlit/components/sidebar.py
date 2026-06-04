"""Sidebar component for Streamlit"""

import streamlit as st


def render_sidebar():
    """Render application sidebar"""
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100?text=FDA+PharmaVigilance", use_column_width=True)
        
        st.markdown("---")
        
        st.markdown("## Navigation")
        st.markdown("""
        - **Dashboard** - Overview and key metrics
        - **Drug Safety** - Individual drug profiles
        - **Demographics** - Patient demographics analysis
        - **Polypharmacy** - Drug combination signals
        """)
        
        st.markdown("---")
        
        st.markdown("## About")
        st.markdown("""
        FDA PharmaVigilance Dashboard provides real-time adverse event
        monitoring and pharmaceutical safety analysis.
        
        **Data Source:** FDA FAERS (Adverse Events Reporting System)
        
        **Last Updated:** Auto-refreshes hourly
        """)
        
        st.markdown("---")
        
        st.markdown("## Support")
        st.markdown("""
        For issues or questions, contact:
        
        📧 data-team@pharmavigilance.local
        """)
