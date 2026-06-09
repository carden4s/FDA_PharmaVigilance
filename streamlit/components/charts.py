"""Chart utilities for Streamlit (dark-themed)."""
import plotly.express as px

_BLUE_SEQ = ["#58a6ff", "#1f6feb", "#388bfd", "#79c0ff", "#a5d6ff"]


def _style(fig, height=400, showlegend=True):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        showlegend=showlegend,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6edf3"),
        title_font=dict(color="#e6edf3", size=18),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def create_bar_chart(data, x, y, title, labels=None, color=None):
    fig = px.bar(data, x=x, y=y, title=title, labels=labels or {},
                 color=color, color_discrete_sequence=_BLUE_SEQ,
                 color_continuous_scale="Blues")
    fig.update_layout(hovermode="x unified")
    return _style(fig, showlegend=False)


def create_pie_chart(data, values, names, title):
    fig = px.pie(data, values=values, names=names, title=title, hole=0.5,
                 color_discrete_sequence=px.colors.sequential.Blues_r)
    return _style(fig)


def create_line_chart(data, x, y, title, labels=None):
    fig = px.line(data, x=x, y=y, title=title, labels=labels or {},
                  markers=True, color_discrete_sequence=_BLUE_SEQ)
    fig.update_layout(hovermode="x unified")
    return _style(fig)


def create_scatter_chart(data, x, y, title, size=None, color=None, labels=None):
    fig = px.scatter(data, x=x, y=y, title=title, size=size, color=color,
                     labels=labels or {}, color_continuous_scale="Blues")
    return _style(fig)