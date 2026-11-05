"""Fraud Investigation Page.

Inspect potential anomalies, review AI-synthesized risk signals,
track reviewed claims in a session-only investigation log, and export audit trails.
"""

from __future__ import annotations

from datetime import datetime
import pandas as pd
import streamlit as st

from api_client import get_high_amount_claims, run_claim_investigation
from components.tables import render_table

st.title("🔍 Fraud & Risk Investigation")
st.caption("AI-powered risk analysis and multi-signal anomaly investigation.")

# Permanent Risk Warning Banner
st.markdown(
    """
    <div style="background-color: #F8D7DA; border-left: 5px solid #DC3545; padding: 10px 14px; border-radius: 4px; margin-bottom: 20px; color: #721C24;">
        <strong>🛡️ Risk indicators only.</strong> Human review is required. No claim has been approved or rejected.
    </div>
    """,
    unsafe_allow_html=True,
)

# ── 1. Claim Selector (Selectbox + Manual Entry) ───────────────
col_sel, col_manual = st.columns([2, 1])

with col_sel:
    high_claims = get_high_amount_claims(limit=25)
    options = {}
    if high_claims:
        for c in high_claims:
            cid = c.get("Claim_ID")
            amt = c.get("Claim_Amount", 0)
            flag = "🚨 Anomaly" if c.get("Is_Fraudulent") else "⚠️ High Value"
            options[f"Claim #{cid} — ${amt:,.2f} ({flag})"] = cid

    selected_label = st.selectbox(
        "Select from High-Amount Claims:",
        options=list(options.keys()) if options else ["No claims loaded"],
    )
    selected_from_dropdown = options.get(selected_label) if options else None

with col_manual:
    manual_id = st.number_input(
        "Or Enter Claim ID Manually:",
        min_value=1,
        step=1,
        value=None,
        placeholder="e.g. 1226",
    )

target_claim_id = int(manual_id) if manual_id else selected_from_dropdown

# Action Button
if st.button("🚀 Run AI Investigation", disabled=not target_claim_id, use_container_width=True):
    with st.spinner(f"Analyzing signals for Claim #{target_claim_id} with Multi-Agent AI..."):
        inv_result = run_claim_investigation(target_claim_id)
        if inv_result:
            st.session_state[f"investigation_{target_claim_id}"] = inv_result

            # Append to session tracker
            if "investigation_tracker" not in st.session_state:
                st.session_state["investigation_tracker"] = []

            # Avoid duplicates in tracker
            existing_ids = [item["claim_id"] for item in st.session_state["investigation_tracker"]]
            if target_claim_id not in existing_ids:
                st.session_state["investigation_tracker"].append({
                    "claim_id": target_claim_id,
                    "risk_level": inv_result.get("risk_level", "UNKNOWN"),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "Under review",
                })

# ── 2. Display Investigation Results ──────────────────────────
if target_claim_id and f"investigation_{target_claim_id}" in st.session_state:
    result = st.session_state[f"investigation_{target_claim_id}"]
    risk_level = result.get("risk_level", "UNKNOWN")

    st.markdown("---")
    st.subheader(f"Investigation Assessment for Claim #{target_claim_id}")

    # Risk Badge
    color_map = {
        "HIGH": ("#DC3545", "#FFF"),
        "MEDIUM": ("#FFA000", "#FFF"),
        "LOW": ("#28A745", "#FFF"),
    }
    bg_color, fg_color = color_map.get(risk_level, ("#6C757D", "#FFF"))

    badge_html = f"""
    <div style="display: inline-block; padding: 6px 16px; background-color: {bg_color}; color: {fg_color}; border-radius: 20px; font-weight: bold; font-size: 1.1rem; margin-bottom: 12px;">
        Risk Level: {risk_level}
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)

    # Risk Signals Cards / Metrics
    signals = result.get("risk_signals", [])
    if signals:
        st.markdown("##### ⚠️ Detected Risk Signals")
        sig_cols = st.columns(min(len(signals), 4))
        for idx, sig in enumerate(signals):
            with sig_cols[idx % 4]:
                st.metric(
                    label=sig.get("signal", "Signal"),
                    value=sig.get("value", "N/A"),
                    delta=f"Severity: {sig.get('severity')}",
                    delta_color="inverse" if sig.get("severity") == "HIGH" else "normal",
                )

    # Narrative Summary
    st.markdown("##### 📝 AI Investigation Summary")
    with st.chat_message("assistant"):
        st.markdown(result.get("summary", "No summary generated."))
        agents = result.get("agents_used", [])
        if agents:
            st.caption(f"🧠 Agents involved: {', '.join(agents)}")

st.markdown("---")

# ── 3. Investigation Status Tracker (Session Only) ────────────
st.subheader("📋 Session Investigation Tracker")
st.caption("Tracks claims investigated in this browser session. Note: This log is stored in browser session state only and is not committed to the database.")

tracker = st.session_state.get("investigation_tracker", [])

if tracker:
    # Allow user to update reviewer status
    for item in tracker:
        cid = item["claim_id"]
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        c1.write(f"**Claim #{cid}**")
        c2.write(f"Risk: `{item['risk_level']}`")
        c3.write(f"Time: {item['timestamp']}")
        with c4:
            new_status = st.selectbox(
                f"Status for #{cid}",
                options=["Open", "Under review", "Reviewed"],
                index=["Open", "Under review", "Reviewed"].index(item["status"]),
                key=f"status_select_{cid}",
                label_visibility="collapsed",
            )
            item["status"] = new_status

    df_tracker = pd.DataFrame(tracker)
    st.markdown("##### Export Audit Trail")
    st.download_button(
        label="📥 Download Investigation Log (CSV)",
        data=df_tracker.to_csv(index=False),
        file_name="session_investigation_log.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No investigations performed yet in this session. Select a claim above and click 'Run AI Investigation'.")
