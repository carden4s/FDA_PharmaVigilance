"""Metric card components"""

import streamlit as st


def metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Display metric card"""
    col = st.column_config.Column(width="small")
    
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


def three_column_metrics(metrics: list):
    """Display three metrics in columns"""
    col1, col2, col3 = st.columns(3)
    
    cols = [col1, col2, col3]
    for i, metric in enumerate(metrics):
        if i < 3:
            cols[i].metric(metric["label"], metric["value"], metric.get("delta"))


def info_box(title: str, content: str):
    """Display info box"""
    st.info(f"**{title}**\n\n{content}")
