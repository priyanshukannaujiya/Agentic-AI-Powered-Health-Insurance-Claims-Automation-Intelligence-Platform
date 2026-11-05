"""Pipeline & Architecture Monitoring Page.

Inspect Databricks Gold-layer table health, table row counts, ingestion freshness,
and enterprise medallion architecture topology.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from api_client import get_pipeline_status, check_health
from components.metrics import render_kpi_card
from components.tables import render_table

st.title("⚡ Pipeline & Architecture Monitoring")
st.caption("Telemetry for Gold-layer Databricks Lakehouse tables, data freshness, and system architecture.")

# ── 1. System Health & Freshness Row ──────────────────────────
health_col1, health_col2 = st.columns([1, 2])
with health_col1:
    is_healthy = check_health()
    if is_healthy:
        st.success("🟢 **FastAPI Service:** Operational")
    else:
        st.error("🔴 **FastAPI Service:** Offline")

with st.spinner("Fetching pipeline status from Databricks Gold layer..."):
    status_payload = get_pipeline_status()

if status_payload:
    ts = status_payload.get("timestamp", "N/A")
    with health_col2:
        st.info(f"🕒 **Last Synchronized (Gold Layer):** `{ts}`")

    st.markdown("---")

    # ── 2. Gold Table Row Counts ──────────────────────────────
    st.subheader("📊 Gold Layer Table Inventory")
    st.caption("Star schema table counts materialized in the Databricks Lakehouse.")

    counts = status_payload.get("table_counts", {})
    fact_count = counts.get("fact_claims", 0)
    member_count = counts.get("dim_member", 0)
    provider_count = counts.get("dim_provider", 0)
    diagnosis_count = counts.get("dim_diagnosis", 0)
    date_count = counts.get("dim_date", 0)

    # Top KPI Metrics for Star Schema
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card("Fact Claims", f"{fact_count:,}", help_text="Core transaction fact table")
    with k2:
        render_kpi_card("Dim Member", f"{member_count:,}", help_text="Insured patients dimension")
    with k3:
        render_kpi_card("Dim Provider", f"{provider_count:,}", help_text="Hospitals and clinics dimension")
    with k4:
        render_kpi_card("Dim Diagnosis", f"{diagnosis_count:,}", help_text="ICD/CPT medical codes dimension")
    with k5:
        render_kpi_card("Dim Date", f"{date_count:,}", help_text="Calendar and timeline dimension")

    st.markdown("##### Detailed Table Catalog")
    table_records = [
        {"Table Name": "default.fact_claims", "Type": "Fact Table", "Row Count": fact_count, "Description": "Claims transactions, amounts, lengths of stay, fraud indicators"},
        {"Table Name": "default.dim_member", "Type": "Dimension", "Row Count": member_count, "Description": "Patient demographics, geography, policy identifiers"},
        {"Table Name": "default.dim_provider", "Type": "Dimension", "Row Count": provider_count, "Description": "Hospitals, clinics, specialties, and provider geography"},
        {"Table Name": "default.dim_diagnosis", "Type": "Dimension", "Row Count": diagnosis_count, "Description": "Diagnosis codes, procedure codes, admission & service classifications"},
        {"Table Name": "default.dim_date", "Type": "Dimension", "Row Count": date_count, "Description": "Date dimensions, years, quarters, months, and day mappings"},
    ]
    df_catalog = pd.DataFrame(table_records)
    render_table(
        df_catalog,
        column_config={
            "Table Name": st.column_config.TextColumn("Table Name"),
            "Type": st.column_config.TextColumn("Layer Type"),
            "Row Count": st.column_config.NumberColumn("Record Count", format="%d"),
            "Description": st.column_config.TextColumn("Schema Description"),
        },
    )
else:
    st.warning("Could not retrieve pipeline status from backend.")

st.markdown("---")

# ── 3. Enterprise Architecture Documentation ───────────────────
st.subheader("🏛️ Enterprise End-to-End Architecture")
st.caption("Standard Medallion Architecture with Agentic AI Layer.")

st.markdown(
    """
```
+---------------------------------------------------------------------------------------------------------+
|                                    ENTERPRISE DATA & AI PIPELINE                                       |
+---------------------------------------------------------------------------------------------------------+

  [ On-Prem / Cloud OLTP ]
         │  (Azure Data Factory Ingestion)
         ▼
  [ Bronze Layer ] ──> Raw Parquet Ingestion (Landing Zone & Audit Logs)
         │  (Delta Lake ETL & Deduplication)
         ▼
  [ Silver Layer ] ──> Cleaned & Conformed Delta Tables (Data Quality Validations)
         │  (Star Schema Modeling & Aggregations)
         ▼
  [ Gold Layer ]   ──> Business Star Schema (Azure Databricks SQL Warehouse)
         │               ├── default.fact_claims
         │               ├── default.dim_member
         │               ├── default.dim_provider
         │               ├── default.dim_diagnosis
         │               └── default.dim_date
         ▼
  [ FastAPI Backend ] (Port 8000)
         │  ├── Database Tool Suite (databricks-sql-connector)
         │  └── Multi-Agent AI Engine (Groq / Llama 3.3 70B)
         ▼
  [ Streamlit UI ] (Port 8501)
            Dashboard | Claims | Fraud Investigation | Analytics | AI Assistant | Pipeline
```
"""
)

# Notice regarding ADF run history
st.info(
    "📌 **Pipeline Orchestration Note:**\n\n"
    "Azure Data Factory (ADF) pipeline triggers, activity run logs, and execution graphs "
    "are managed directly via the **Azure Portal**. In compliance with enterprise security policies, "
    "operational run statuses are viewed in the Azure ADF Monitoring Hub rather than simulated in this frontend."
)
