"""Analytics Page.

Multi-dimensional portfolio analytics with interactive Plotly visualizations,
underlying data tables with custom column configurations, filters, and CSV export.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import (
    get_claims_by_state,
    get_top_providers,
    get_monthly_trend,
    get_claims_by_provider_type,
)
from components.charts import create_bar_chart, create_line_chart, create_donut_chart
from components.tables import render_table

st.title("📈 Portfolio Analytics")
st.caption("Deep-dive analytics across geographic distributions, provider facilities, and temporal trends.")

# ── Global Filters ─────────────────────────────────────────────
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    year_filter = st.selectbox(
        "Filter by Year (Monthly Trend)",
        options=["All", 2020, 2021, 2022, 2023, 2024, 2025],
        index=0,
    )
with col_f2:
    limit_slider = st.slider("Record Limit (States / Providers)", 5, 50, 15, 5)

st.markdown("---")

tab_state, tab_providers, tab_trend, tab_prov_type = st.tabs([
    "📍 By State", "🏥 Top Providers", "📅 Monthly Trend", "🏢 Provider Type",
])

# ── Tab 1: By State ──
with tab_state:
    st.subheader("Geographic Distribution of Claims")
    with st.spinner("Fetching claims by state..."):
        state_data = get_claims_by_state(limit=limit_slider)

    if state_data:
        df_state = pd.DataFrame(state_data)
        fig_state = create_bar_chart(
            df_state, x="state", y="claim_count",
            title=f"Top {len(df_state)} States by Claim Volume",
            labels={"state": "Patient State", "claim_count": "Total Claims"},
        )
        st.plotly_chart(fig_state, use_container_width=True)

        st.markdown("##### Underlying State Data")
        render_table(
            df_state,
            column_config={
                "state": st.column_config.TextColumn("State"),
                "claim_count": st.column_config.NumberColumn("Total Claims", format="%d"),
                "total_amount": st.column_config.NumberColumn("Total Amount", format="$%,.2f"),
            },
        )
        st.download_button(
            label="📥 Download State Data (CSV)",
            data=df_state.to_csv(index=False),
            file_name="claims_by_state.csv",
            mime="text/csv",
        )
    else:
        st.info("No state data available.")

# ── Tab 2: Top Providers ──
with tab_providers:
    st.subheader("Top Healthcare Providers by Claim Volume")
    with st.spinner("Fetching top providers..."):
        provider_data = get_top_providers(limit=limit_slider)

    if provider_data:
        df_provider = pd.DataFrame(provider_data)
        df_provider["provider_label"] = df_provider.apply(
            lambda r: f"Hospital #{r['Hospital_ID']} ({r.get('Provider_City', '')})", axis=1
        )
        fig_prov = create_bar_chart(
            df_provider, x="provider_label", y="claim_count",
            title=f"Top {len(df_provider)} Providers by Claim Count",
            labels={"provider_label": "Provider / Hospital", "claim_count": "Claims Count"},
        )
        st.plotly_chart(fig_prov, use_container_width=True)

        st.markdown("##### Underlying Provider Data")
        render_table(
            df_provider[["Hospital_ID", "Provider_Type", "Provider_Specialty", "Provider_City", "Provider_State", "claim_count", "total_amount", "avg_amount"]],
            column_config={
                "Hospital_ID": st.column_config.NumberColumn("Hospital ID", format="%d"),
                "Provider_Type": st.column_config.TextColumn("Facility Type"),
                "Provider_Specialty": st.column_config.TextColumn("Specialty"),
                "Provider_City": st.column_config.TextColumn("City"),
                "Provider_State": st.column_config.TextColumn("State"),
                "claim_count": st.column_config.NumberColumn("Claims", format="%d"),
                "total_amount": st.column_config.NumberColumn("Total Amount", format="$%,.2f"),
                "avg_amount": st.column_config.NumberColumn("Avg Claim", format="$%,.2f"),
            },
        )
        st.download_button(
            label="📥 Download Provider Data (CSV)",
            data=df_provider.to_csv(index=False),
            file_name="top_providers.csv",
            mime="text/csv",
        )
    else:
        st.info("No provider data available.")

# ── Tab 3: Monthly Trend ──
with tab_trend:
    st.subheader("Claims Volume and Expenditure Trends")
    selected_year = None if year_filter == "All" else int(year_filter)
    with st.spinner("Fetching monthly trend..."):
        trend_data = get_monthly_trend(year=selected_year)

    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        df_trend["period"] = df_trend.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1)
        df_trend = df_trend.sort_values("period")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            fig_count = create_line_chart(
                df_trend,
                x="period",
                y="claim_count",
                title=f"Claim Volume Trend ({year_filter})",
                labels={"period": "Period", "claim_count": "Claims Count"},
            )
            st.plotly_chart(fig_count, use_container_width=True)

        with chart_col2:
            fig_amt = create_line_chart(
                df_trend,
                x="period",
                y="total_amount",
                title=f"Total Expenditure Trend ({year_filter})",
                labels={"period": "Period", "total_amount": "Total Amount ($)"},
            )
            st.plotly_chart(fig_amt, use_container_width=True)

        st.markdown("##### Underlying Trend Data")
        render_table(
            df_trend[["year", "month", "claim_count", "total_amount"]],
            column_config={
                "year": st.column_config.NumberColumn("Year", format="%d"),
                "month": st.column_config.NumberColumn("Month", format="%02d"),
                "claim_count": st.column_config.NumberColumn("Total Claims", format="%d"),
                "total_amount": st.column_config.NumberColumn("Total Amount", format="$%,.2f"),
            },
        )
        st.download_button(
            label="📥 Download Monthly Trend Data (CSV)",
            data=df_trend.to_csv(index=False),
            file_name="monthly_trend.csv",
            mime="text/csv",
        )
    else:
        st.info("No trend data available for selected filter.")

# ── Tab 4: Provider Type ──
with tab_prov_type:
    st.subheader("Distribution Across Facility & Provider Types")
    with st.spinner("Fetching provider type breakdown..."):
        type_data = get_claims_by_provider_type()

    if type_data:
        df_type = pd.DataFrame(type_data)
        fig_donut = create_donut_chart(
            df_type, names="provider_type", values="claim_count",
            title="Claim Proportion by Provider Facility",
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("##### Underlying Facility Breakdown")
        render_table(
            df_type,
            column_config={
                "provider_type": st.column_config.TextColumn("Provider Type"),
                "claim_count": st.column_config.NumberColumn("Claim Count", format="%d"),
                "total_amount": st.column_config.NumberColumn("Total Amount", format="$%,.2f"),
                "avg_amount": st.column_config.NumberColumn("Average Amount", format="$%,.2f"),
            },
        )
        st.download_button(
            label="📥 Download Provider Type Data (CSV)",
            data=df_type.to_csv(index=False),
            file_name="provider_type_breakdown.csv",
            mime="text/csv",
        )
    else:
        st.info("No provider type data available.")
