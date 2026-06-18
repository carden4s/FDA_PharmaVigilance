# Sidebar component (Spanish)
# Co-authored with CoCo
"""Barra lateral del panel de FarmacoVigilancia."""
import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sb-brand">💊 FarmacoVigilancia</div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-sub">Análisis de eventos adversos · FDA</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown("#### Navegación")
        st.markdown(
            "🏥 **Panel principal** — resumen y métricas clave\n\n"
            "📈 **Señales PRR/ROR** — desproporcionalidad\n\n"
            "🧬 **Reacciones** — por medicamento\n\n"
            "👥 **Demografía** — perfil de pacientes\n\n"
            "⚗️ **Polifarmacia** — combinaciones de fármacos"
        )
        st.divider()

        st.markdown("#### Fuente de datos")
        st.markdown(
            '<span class="badge">openFDA FAERS</span>'
            '<span class="badge">Ventana 3 años</span>'
            '<span class="badge">Actualizado por dbt</span>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sb-card">Monitoreo de eventos adversos y análisis de '
            'seguridad farmacéutica.<br><br>'
            '⚠️ Los reportes de FAERS son <b>espontáneos</b>: muestran '
            '<b>asociaciones de notificación</b>, no causalidad ni incidencia.</div>',
            unsafe_allow_html=True,
        )