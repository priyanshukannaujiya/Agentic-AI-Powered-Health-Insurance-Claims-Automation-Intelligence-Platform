"""Claims Management Page.

Search single claim records, inspect multi-dimensional details (patient,
provider, diagnosis), trigger on-demand AI claim summarization, and paginate
through the complete claims register.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import get_claims, get_claim_by_id, send_chat_message
from components.tables import render_table

st.title("📋 Claims Management")
st.caption("Inspect and audit insurance claims with comprehensive patient, provider, and diagnosis details.")

# ── 1. Search Box for Single Claim ───────────────────────────
st.subheader("🔍 Search Claim Details")
search_col1, search_col2 = st.columns([3, 1])

with search_col1:
    search_id = st.number_input(
        "Enter Claim ID (e.g. 1, 1226, 18874)",
        min_value=1,
        step=1,
        value=None,
        placeholder="Type a Claim ID...",
    )

with search_col2:
    st.write("")
    st.write("")
    search_clicked = st.button("Search Claim", use_container_width=True)

if search_clicked and search_id:
    st.session_state["active_claim_id"] = int(search_id)

active_id = st.session_state.get("active_claim_id")

if active_id:
    with st.spinner(f"Fetching details for Claim #{active_id}..."):
        claim = get_claim_by_id(active_id)

    if claim:
        st.success(f"Displaying Claim #{active_id}")

        # Section 1: Financial & Core Claim Details
        st.markdown("#### 💳 Claim & Financial Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Claim Amount", f"${claim.get('Claim_Amount', 0):,.2f}")
        m2.metric("Deductible", f"${claim.get('Deductible_Amount', 0):,.2f}")
        m3.metric("Co-Pay", f"${claim.get('CoPay_Amount', 0):,.2f}")
        m4.metric("Length of Stay", f"{claim.get('Length_of_Stay_Days', 0)} days")

        c1, c2, c3, c4 = st.columns(4)
        c1.write(f"**Claim Date:** {claim.get('Claim_Date', 'N/A')}")
        c2.write(f"**Service Date:** {claim.get('Service_Date', 'N/A')}")
        c3.write(f"**Late Submission:** {'⚠️ Yes' if claim.get('Claim_Submitted_Late') else '✅ No'}")
        c4.write(f"**Flagged Anomaly:** {'🚨 Yes' if claim.get('Is_Fraudulent') else '✅ No'}")

        st.markdown("---")

        # Section 2: Patient & Provider Information
        col_patient, col_provider = st.columns(2)
        with col_patient:
            st.markdown("#### 👤 Patient Profile")
            st.write(f"**Patient ID:** `{claim.get('Patient_ID', 'N/A')}`")
            st.write(f"**Policy Number:** `{claim.get('Policy_Number', 'N/A')}`")
            st.write(f"**Age / Gender:** {claim.get('Patient_Age', 'N/A')} yrs / {claim.get('Patient_Gender', 'N/A')}")
            st.write(f"**Location:** {claim.get('Patient_City', 'N/A')}, {claim.get('Patient_State', 'N/A')}")
            st.write(f"**Prior Claims (Patient):** {claim.get('Number_of_Previous_Claims_Patient', 0)}")

        with col_provider:
            st.markdown("#### 🏥 Provider Information")
            st.write(f"**Hospital / Facility ID:** `{claim.get('Hospital_ID', 'N/A')}`")
            st.write(f"**Facility Type:** {claim.get('Provider_Type', 'N/A')}")
            st.write(f"**Specialty:** {claim.get('Provider_Specialty', 'N/A')}")
            st.write(f"**Location:** {claim.get('Provider_City', 'N/A')}, {claim.get('Provider_State', 'N/A')}")
            st.write(f"**Prior Claims (Provider):** {claim.get('Number_of_Previous_Claims_Provider', 0)}")

        st.markdown("---")

        # Section 3: Clinical & Diagnosis
        st.markdown("#### 🩺 Clinical & Diagnosis Codes")
        d1, d2, d3, d4 = st.columns(4)
        d1.write(f"**Diagnosis Code:** `{claim.get('Diagnosis_Code', 'N/A')}`")
        d2.write(f"**Procedure Code:** `{claim.get('Procedure_Code', 'N/A')}`")
        d3.write(f"**Admission Type:** {claim.get('Admission_Type', 'N/A')}")
        d4.write(f"**Service / Discharge:** {claim.get('Service_Type', 'N/A')} / {claim.get('Discharge_Type', 'N/A')}")

        st.markdown("---")

        # Section 4: AI Summary Button
        if st.button("✨ Summarize this claim with AI", key="btn_summarize_claim"):
            with st.spinner("Analyzing claim details with AI..."):
                prompt = (
                    f"Please summarize and analyze Claim #{active_id}. "
                    f"Patient ID: {claim.get('Patient_ID')}, Amount: ${claim.get('Claim_Amount', 0):,.2f}, "
                    f"Provider: {claim.get('Provider_Type')} ({claim.get('Provider_Specialty')}), "
                    f"Diagnosis: {claim.get('Diagnosis_Code')}, Procedure: {claim.get('Procedure_Code')}, "
                    f"Length of Stay: {claim.get('Length_of_Stay_Days')} days, "
                    f"Late Submission: {claim.get('Claim_Submitted_Late')}, "
                    f"Flagged Anomaly: {claim.get('Is_Fraudulent')}."
                )
                ai_resp = send_chat_message(prompt)
                if ai_resp and "response" in ai_resp:
                    st.session_state[f"claim_summary_{active_id}"] = ai_resp

        if f"claim_summary_{active_id}" in st.session_state:
            summary = st.session_state[f"claim_summary_{active_id}"]
            with st.chat_message("assistant"):
                st.markdown(summary.get("response", ""))
                agents = summary.get("agents_used", [])
                if agents:
                    st.caption(f"🧠 Agents involved: {', '.join(agents)}")
    else:
        st.warning(f"Claim ID #{active_id} was not found in the database. Please verify the ID.")

st.markdown("---")

# ── 2. Paginated Claims Table ─────────────────────────────────
st.subheader("📑 Claims Registry Browser")

# Pagination State Initialization
if "claims_page" not in st.session_state:
    st.session_state["claims_page"] = 0

ctrl1, ctrl2, ctrl3 = st.columns([2, 1, 1])
with ctrl1:
    page_size = st.selectbox("Rows per page", options=[10, 25, 50], index=1)

current_page = st.session_state["claims_page"]
offset = current_page * page_size

with st.spinner("Loading claims page..."):
    claims_payload = get_claims(limit=page_size, offset=offset)

if claims_payload:
    total_records = claims_payload.get("total", 0)
    claims_list = claims_payload.get("claims", [])
    max_pages = max(1, (total_records + page_size - 1) // page_size)

    with ctrl2:
        st.caption(f"Page {current_page + 1} of {max_pages:,}")
        st.caption(f"Total: {total_records:,} records")

    with ctrl3:
        btn_prev, btn_next = st.columns(2)
        with btn_prev:
            if st.button("◀ Prev", disabled=(current_page == 0)):
                st.session_state["claims_page"] = max(0, current_page - 1)
                st.rerun()
        with btn_next:
            if st.button("Next ▶", disabled=(current_page >= max_pages - 1)):
                st.session_state["claims_page"] = min(max_pages - 1, current_page + 1)
                st.rerun()

    if claims_list:
        df_claims = pd.DataFrame(claims_list)
        # Select concise display columns for registry view
        display_cols = [
            "Claim_ID", "Claim_Date", "Claim_Amount", "Patient_ID",
            "Patient_State", "Provider_Type", "Diagnosis_Code",
            "Claim_Submitted_Late", "Is_Fraudulent"
        ]
        available_cols = [c for c in display_cols if c in df_claims.columns]
        render_table(
            df_claims[available_cols],
            column_config={
                "Claim_ID": st.column_config.NumberColumn("Claim ID", format="%d"),
                "Claim_Date": st.column_config.DateColumn("Date"),
                "Claim_Amount": st.column_config.NumberColumn("Amount", format="$%,.2f"),
                "Patient_ID": st.column_config.NumberColumn("Patient ID", format="%d"),
                "Patient_State": st.column_config.TextColumn("State"),
                "Provider_Type": st.column_config.TextColumn("Provider Type"),
                "Diagnosis_Code": st.column_config.TextColumn("Diagnosis"),
                "Claim_Submitted_Late": st.column_config.CheckboxColumn("Late"),
                "Is_Fraudulent": st.column_config.CheckboxColumn("Flagged"),
            },
        )
    else:
        st.info("No claims found for this page.")
else:
    st.info("Claims data could not be retrieved.")
