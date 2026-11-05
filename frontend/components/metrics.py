"""Reusable Metric Card Components."""

from __future__ import annotations

import streamlit as st


def render_kpi_card(
    label: str,
    value: str | int | float,
    help_text: str | None = None,
    delta: str | None = None,
    delta_color: str = "normal",
):
    """Render a styled KPI card metric."""
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )

