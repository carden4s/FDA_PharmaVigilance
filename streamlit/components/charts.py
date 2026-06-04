"""Chart utilities for Streamlit"""

import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any


def create_bar_chart(data, x, y, title, labels=None, color=None):
    """Create bar chart"""
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        labels=labels or {},
        color=color,
        template="plotly_white"
    )
    fig.update_layout(
        hovermode="x unified",
        height=400,
        showlegend=False
    )
    return fig


def create_pie_chart(data, values, names, title):
    """Create pie chart"""
    fig = px.pie(
        data,
        values=values,
        names=names,
        title=title,
        template="plotly_white"
    )
    fig.update_layout(height=400)
    return fig


def create_line_chart(data, x, y, title, labels=None):
    """Create line chart"""
    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        labels=labels or {},
        template="plotly_white",
        markers=True
    )
    fig.update_layout(
        hovermode="x unified",
        height=400
    )
    return fig


def create_scatter_chart(data, x, y, title, size=None, color=None, labels=None):
    """Create scatter chart"""
    fig = px.scatter(
        data,
        x=x,
        y=y,
        title=title,
        size=size,
        color=color,
        labels=labels or {},
        template="plotly_white"
    )
    fig.update_layout(height=400)
    return fig
