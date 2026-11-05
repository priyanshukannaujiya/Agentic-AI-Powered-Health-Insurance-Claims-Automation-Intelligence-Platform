"""Dashboard Page.

Executive summary of claims portfolio, key metrics, distribution charts,
high-value claims monitor, and on-demand AI executive summary.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import (
    get_analytics_summary,
    get_claims_by_state,
    get_monthly_trend,
    get_claims_by_provider_type,
    get_high_amount_claims,
    send_chat_message,
)
from components.metrics import render_kpi_card
from components.charts import create_bar_chart, create_line_chart, create_donut_chart
from components.tables import render_table

st.title("📊 Claims Portfolio Dashboard")
st.caption("Real-time executive intelligence and risk metrics across the health insurance portfolio.")

# ── 1. KPI Cards Row ──────────────────────────────────────────
with st.spinner("Loading portfolio metrics..."):
    analytics = get_analytics_summary()

if analytics:
    total_claims = analytics.get("total_claims", 0)
    distinct_patients = analytics.get("distinct_patients", 0)
    total_amount = analytics.get("total_claim_amount", 0.0)
    avg_amount = analytics.get("avg_claim_amount", 0.0)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        render_kpi_card("Total Claims", f"{total_claims:,}")
    with kpi2:
        render_kpi_card("Distinct Patients", f"{distinct_patients:,}")
    with kpi3:
        render_kpi_card("Total Claim Amount", f"${total_amount:,.2f}")
    with kpi4:
        render_kpi_card("Average Claim Amount", f"${avg_amount:,.2f}")
else:
    st.info("Portfolio metrics currently unavailable.")

st.markdown("---")

# ── 2. On-Demand AI Executive Summary ──────────────────────────
col_summary_btn, col_summary_info = st.columns([1, 4])
with col_summary_btn:
    generate_summary = st.button("✨ AI Executive Summary", use_container_width=True)

with col_summary_info:
    st.caption("Generate a high-level executive briefing synthesized by the multi-agent AI system.")

if generate_summary:
    with st.spinner("Analyzing portfolio with AI agent..."):
        ai_resp = send_chat_message("Give a short executive summary of the claims portfolio.")
        if ai_resp and "response" in ai_resp:
            st.session_state["dashboard_ai_summary"] = ai_resp

if "dashboard_ai_summary" in st.session_state:
    summary_data = st.session_state["dashboard_ai_summary"]
    with st.chat_message("assistant"):
        st.markdown(summary_data.get("response", ""))
        agents = summary_data.get("agents_used", [])
        if agents:
            st.caption(f"🧠 Agents involved: {', '.join(agents)}")

st.markdown("---")

# ── 3. Visual Charts Row ───────────────────────────────────────
st.subheader("📈 Portfolio Distribution & Trends")

tab_geo, tab_trend, tab_facility = st.tabs([
    "Claims by State",
    "Monthly Trend",
    "Claims by Provider Type"
])

with tab_geo:
    with st.spinner("Loading state distribution..."):
        state_data = get_claims_by_state(limit=15)
    if state_data:
        df_state = pd.DataFrame(state_data)
        fig_state = create_bar_chart(
            df_state,
            x="state",
            y="claim_count",
            title="Top 15 States by Claim Volume",
            labels={"state": "Patient State", "claim_count": "Total Claims"},
        )
        st.plotly_chart(fig_state, use_container_width=True)
    else:
        st.info("State distribution data unavailable.")

with tab_trend:
    with st.spinner("Loading monthly trends..."):
        trend_data = get_monthly_trend()
    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        df_trend["period"] = df_trend.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1)
        df_trend = df_trend.sort_values("period")
        fig_trend = create_line_chart(
            df_trend,
            x="period",
            y="claim_count",
            title="Claims Volume Trend Over Time",
            labels={"period": "Year-Month", "claim_count": "Claims Count"},
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Monthly trend data unavailable.")

with tab_facility:
    with st.spinner("Loading provider type breakdown..."):
        provider_type_data = get_claims_by_provider_type()
    if provider_type_data:
        df_prov = pd.DataFrame(provider_type_data)
        fig_prov = create_donut_chart(
            df_prov,
            names="provider_type",
            values="claim_count",
            title="Claim Distribution by Facility / Provider Type",
        )
        st.plotly_chart(fig_prov, use_container_width=True)
    else:
        st.info("Provider type data unavailable.")

st.markdown("---")

# ── 4. Top High-Amount Claims Monitor ─────────────────────────
st.subheader("🚨 Top High-Amount Claims Monitor")
st.caption("Claims with the highest financial exposure. These claims are prioritized for anomaly review.")

with st.spinner("Loading high-amount claims..."):
    high_claims = get_high_amount_claims(limit=10)

if high_claims:
    df_high = pd.DataFrame(high_claims)
    render_table(
        df_high,
        column_config={
            "Claim_ID": st.column_config.NumberColumn("Claim ID", format="%d"),
            "Claim_Amount": st.column_config.NumberColumn("Claim Amount", format="$%,.2f"),
            "Claim_Date": st.column_config.DateColumn("Date of Claim"),
            "Is_Fraudulent": st.column_config.CheckboxColumn("Flagged Anomaly"),
            "Claim_Submitted_Late": st.column_config.CheckboxColumn("Late Submission"),
            "Number_of_Procedures": st.column_config.NumberColumn("Procedures"),
            "Length_of_Stay_Days": st.column_config.NumberColumn("Length of Stay (Days)"),
            "Patient_State": st.column_config.TextColumn("State"),
            "Provider_Type": st.column_config.TextColumn("Provider Type"),
            "Provider_Specialty": st.column_config.TextColumn("Specialty"),
        },
    )
else:
    st.info("No high-amount claims data available.")
