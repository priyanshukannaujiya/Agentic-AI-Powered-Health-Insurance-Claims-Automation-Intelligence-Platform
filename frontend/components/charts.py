"""Reusable Plotly Chart Components."""

from __future__ import annotations

from typing import Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Consistent color palette for enterprise healthcare styling
PRIMARY_COLOR = "#0066FF"
ACCENT_COLOR = "#00B4D8"
WARN_COLOR = "#FFA000"
ALERT_COLOR = "#E63946"
NEUTRAL_COLOR = "#4A5568"
PALETTE = px.colors.qualitative.Prism


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    labels: dict[str, str] | None = None,
    orientation: str = "v",
) -> go.Figure:
    """Create a standardized bar chart with tooltips and clean styling."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        labels=labels or {},
        orientation=orientation,
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title=labels.get(x, x) if labels else x,
        yaxis_title=labels.get(y, y) if labels else y,
    )
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    labels: dict[str, str] | None = None,
) -> go.Figure:
    """Create a standardized line chart with markers."""
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        labels=labels or {},
        markers=True,
        color_discrete_sequence=[PRIMARY_COLOR],
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_title=labels.get(x, x) if labels else x,
        yaxis_title=labels.get(y, y) if labels else y,
    )
    return fig


def create_donut_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
) -> go.Figure:
    """Create a standardized donut chart."""
    fig = px.pie(
        df,
        names=names,
        values=values,
        title=title,
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig

