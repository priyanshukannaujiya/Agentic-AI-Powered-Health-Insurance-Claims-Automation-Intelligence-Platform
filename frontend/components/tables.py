"""Reusable DataFrame and Table Display Helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_table(
    df: pd.DataFrame,
    column_config: dict | None = None,
    hide_index: bool = True,
    use_container_width: bool = True,
):
    """Render a styled dataframe using st.dataframe with custom formatting."""
    st.dataframe(
        df,
        column_config=column_config,
        hide_index=hide_index,
        use_container_width=use_container_width,
    )

