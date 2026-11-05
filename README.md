# 🏥 Agentic AI-Powered Health Insurance Claims Automation & Intelligence Platform

An enterprise-grade, read-only analytics and intelligence platform for health insurance claims operations. Built with **FastAPI**, **Azure Databricks (Lakehouse Star Schema)**, **Groq Multi-Agent LLM System**, and a **Streamlit** frontend.

---

> 📦 **DATA INGESTION: Batch Processed Pipeline Data**  
> All data in this platform is batch-processed and ingested via scheduled Azure Data Factory ETL pipelines into the Azure Databricks Gold Lakehouse layer. Risk indicators and anomaly flags are decision-support signals requiring human review. No claim is approved, rejected, or modified automatically by this system.

---

## 🏛️ System Architecture

```
[ On-Prem / Cloud OLTP ]
       │  (Azure Data Factory Ingestion)
       ▼
[ Bronze Layer ]  ──> Raw Parquet Ingestion (Landing Zone & Audit Logs)
       │  (Delta Lake ETL & Deduplication)
       ▼
[ Silver Layer ]  ──> Cleaned & Conformed Delta Tables (Data Quality Validations)
       │  (Star Schema Modeling & Aggregations)
       ▼
[ Gold Layer ]    ──> Star Schema (Azure Databricks SQL Warehouse)
       │                 ├── default.fact_claims (20,072 rows)
       │                 ├── default.dim_member  (19,994 rows)
       │                 ├── default.dim_provider (1,000 rows)
       │                 ├── default.dim_diagnosis (16,856 rows)
       │                 └── default.dim_date     (3,741 rows)
       ▼
[ FastAPI Backend ] (Port 8000)
       │  ├── Read-Only SQL Tool Suite (databricks-sql-connector)
       │  └── Multi-Agent AI Engine (Groq Llama / Qwen)
       ▼
[ Streamlit UI ] (Port 8501)
          Dashboard | Claims | Fraud Investigation | Analytics | AI Assistant | Pipeline
```

---

## 🚀 Quickstart & Run Instructions

### 1. Prerequisites
- Python 3.10 or 3.11
- Active Azure Databricks SQL Warehouse credentials
- Groq API Key

### 2. Environment Configuration
Ensure `.env` exists in the project root:
```env
# Azure Databricks Connection Settings
DATABRICKS_SERVER_HOSTNAME=adb-7405616659701821.1.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/fb36cb95ba65e26a
DATABRICKS_TOKEN=dapi_your_databricks_token_here

# Groq API Key & Model (for LLM multi-agent engine)
GROQ_API_KEY=gsk_your_groq_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

Ensure `frontend/.env` contains the API base URL:
```env
API_BASE_URL=http://localhost:8000
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Running the Application

Open two terminal windows:

#### **Terminal 1: FastAPI Backend**
```bash
uvicorn backend.main:app --reload
```
*Backend runs at `http://localhost:8000`. Interactive OpenAPI documentation available at `http://localhost:8000/docs`.*

#### **Terminal 2: Streamlit Frontend**
```bash
streamlit run frontend/app.py
```
*Frontend opens automatically at `http://localhost:8501`.*

---

## 🖥️ Platform Modules & Pages

1. **📊 Executive Dashboard (`frontend/pages/dashboard.py`):**
   - High-level KPIs: Total claims, distinct patients, gross claim expenditure, and average claim amount.
   - Interactive Plotly visualizations for geographic distribution, monthly trends, and provider types.
   - Top high-amount claims monitor.
   - On-demand AI executive summary generator (`✨ AI Executive Summary`).

2. **📋 Claims Management (`frontend/pages/claims.py`):**
   - Fast lookup for any `Claim_ID` with structured breakdowns across financial metrics, patient profile, provider details, and diagnosis codes.
   - On-demand AI claim analysis (`✨ Summarize this claim with AI`).
   - Paginated claims registry browser (10, 25, or 50 rows per page).

3. **🔍 Fraud & Risk Investigation (`frontend/pages/fraud_investigation.py`):**
   - Anomaly detector analyzing multi-signal vectors (claim amount vs provider average ratio, extended length of stay, late submission, provider claim frequency).
   - Color-coded risk badges (**LOW**, **MEDIUM**, **HIGH**).
   - AI-generated structured investigation narrative with recommended audit actions.
   - Session-only review status tracker with CSV export.

4. **📈 Portfolio Analytics (`frontend/pages/analytics.py`):**
   - Multi-tab analytics: **By State**, **Top Providers**, **Monthly Trend**, and **Provider Type**.
   - Year filter and record limit sliders.
   - Interactive Plotly charts with tooltips.
   - Formatted underlying tables and CSV export buttons on every tab.

5. **🤖 AI Claims Assistant (`frontend/pages/ai_assistant.py`):**
   - Multi-agent conversational Copilot with thread-based context memory.
   - Visual attribution badges showing which agents contributed (`Claims Analyst Agent`, `Fraud Detection Agent`, `Analytics Agent`).
   - Quick prompt shortcuts in the sidebar.

6. **⚡ Pipeline & Architecture Monitoring (`frontend/pages/pipeline_monitoring.py`):**
   - Live telemetry and row counts for all 5 Gold-layer tables (`fact_claims`, `dim_member`, `dim_provider`, `dim_diagnosis`, `dim_date`).
   - Ingestion freshness timestamp.
   - Architecture documentation and enterprise medallion lineage.

---

## 🔒 Architectural Guardrails
- **Strict Separation of Concerns:** The Streamlit frontend interacts strictly over HTTP via `frontend/api_client.py`. It never imports `databricks`, never inspects Lakehouse credentials, and never executes SQL directly.
- **Read-Only Enforced:** Zero mutation, rejection, or approval buttons exist in the UI.
- **Resilient Caching & Error Handling:** Read-only data endpoints leverage `st.cache_data` (60-second TTL), timeouts (30s / 90s for LLMs), and friendly warning states without raw tracebacks.
