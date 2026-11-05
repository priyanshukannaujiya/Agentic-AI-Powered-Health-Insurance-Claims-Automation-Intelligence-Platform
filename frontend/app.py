"""Agentic AI-Powered Health Insurance Claims Automation & Intelligence Platform.

Main Streamlit Application Entrypoint.
"""

from __future__ import annotations

import streamlit as st
from api_client import check_health

# Configure page settings
st.set_page_config(
    page_title="Claims Intelligence Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar brand & system status
with st.sidebar:
    st.markdown("### 🏥 Claims Intelligence")
    st.caption("Agentic AI-Powered Automation & Analytics")
    st.divider()

    # Backend Connection Status Indicator
    is_healthy = check_health()
    if is_healthy:
        st.markdown("🟢 **API Status:** Connected (`Online`)")
    else:
        st.markdown("🔴 **API Status:** Disconnected (`Offline`)")
        st.caption("Ensure FastAPI is running at `http://localhost:8000`")

    st.divider()

    # Batch Process Pipeline Status in Sidebar
    st.info(
        "📦 **Batch Processed Data**\n\n"
        "Ingested via scheduled Azure Data Factory ETL into Databricks Lakehouse (Gold Layer). "
        "Risk indicators require human review."
    )

# Top Banner Notice for Pipeline Ingestion Mode
st.markdown(
    """
    <div style="background-color: #E8F4FD; border-left: 5px solid #0066FF; padding: 10px 14px; border-radius: 4px; margin-bottom: 20px; color: #0C5460; font-size: 0.95rem;">
        <strong>📦 Batch Processed Pipeline Data:</strong> Ingested from enterprise claims lakehouse via scheduled ADF batch processing. Risk indicators are decision-support signals and require human review.
    </div>
    """,
    unsafe_allow_html=True,
)

# Modern Streamlit Navigation (st.navigation with st.Page)
pages = {
    "Operations": [
        st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True),
        st.Page("pages/claims.py", title="Claims Management", icon="📋"),
        st.Page("pages/fraud_investigation.py", title="Fraud Investigation", icon="🔍"),
    ],
    "Analytics & AI": [
        st.Page("pages/analytics.py", title="Analytics", icon="📈"),
        st.Page("pages/ai_assistant.py", title="AI Assistant", icon="🤖"),
        st.Page("pages/pipeline_monitoring.py", title="Pipeline Monitoring", icon="⚡"),
    ],
}

nav = st.navigation(pages)
nav.run()

