"""Chart utilities for Streamlit (dark-themed)."""
import plotly.express as px
import plotly.graph_objects as go

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

def create_forest_plot(data, point, lower, upper, label, title, ref_line=1.0, height=600):
    """Forest plot: point estimate with 95% CI error bars (log x-axis, reference line).

    data: DataFrame; point/lower/upper: numeric column names; label: y-axis category column.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data[point], y=data[label],
        mode="markers",
        marker=dict(color="#58a6ff", size=9),
        error_x=dict(
            type="data", symmetric=False,
            array=(data[upper] - data[point]),
            arrayminus=(data[point] - data[lower]),
            color="#388bfd", thickness=1.5, width=4,
        ),
        hovertemplate="%{y}<br>" + point + ": %{x:.2f}<extra></extra>",
    ))
    fig.add_vline(x=ref_line, line_dash="dash", line_color="#8b949e")
    fig.update_layout(
        template="plotly_dark", height=height, title=title,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6edf3"), title_font=dict(color="#e6edf3", size=18),
        xaxis_type="log", xaxis_title=f"{point} (escala log · IC 95%)", yaxis_title="",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig