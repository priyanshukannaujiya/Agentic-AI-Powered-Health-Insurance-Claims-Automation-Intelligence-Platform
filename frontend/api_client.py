"""Frontend API client.

Handles all HTTP communication with the FastAPI backend.
Enforces timeouts, error handling, and st.cache_data for read-only endpoints.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
import requests
import streamlit as st
from dotenv import load_dotenv

# Load frontend/.env or root .env
FRONTEND_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=FRONTEND_DIR / ".env")
load_dotenv(dotenv_path=FRONTEND_DIR.parent / ".env")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

DEFAULT_TIMEOUT = 30
LLM_TIMEOUT = 90


def _request(
    method: str,
    endpoint: str,
    params: Optional[dict[str, Any]] = None,
    json_data: Optional[dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[Any]:
    """Single central dispatcher for all HTTP requests to FastAPI."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=timeout,
        )
        if response.status_code == 404:
            st.warning(f"Resource not found: {endpoint}")
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"Request timed out while contacting backend ({endpoint}). Please try again later.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Unable to connect to backend at {API_BASE_URL}. Ensure the FastAPI server is running.")
        return None
    except requests.exceptions.HTTPError as e:
        detail = "Unknown error"
        try:
            detail = response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"Backend API Error ({response.status_code}): {detail}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while communicating with the API: {e}")
        return None


# ── Health (Cache short or check dynamically) ──

def check_health() -> bool:
    """Check if the backend API is alive and reachable."""
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return res.status_code == 200 and res.json().get("status") == "healthy"
    except Exception:
        return False


# ── Cached Read-Only Data Endpoints (TTL = 60s) ──

@st.cache_data(ttl=60, show_spinner=False)
def get_analytics_summary() -> Optional[dict[str, Any]]:
    return _request("GET", "/analytics")


@st.cache_data(ttl=60, show_spinner=False)
def get_claims_by_state(limit: int = 50) -> Optional[list[dict[str, Any]]]:
    return _request("GET", "/analytics/by-state", params={"limit": limit})


@st.cache_data(ttl=60, show_spinner=False)
def get_top_providers(limit: int = 20) -> Optional[list[dict[str, Any]]]:
    return _request("GET", "/analytics/top-providers", params={"limit": limit})


@st.cache_data(ttl=60, show_spinner=False)
def get_monthly_trend(year: Optional[int] = None) -> Optional[list[dict[str, Any]]]:
    params = {"year": year} if year else {}
    return _request("GET", "/analytics/monthly-trend", params=params)


@st.cache_data(ttl=60, show_spinner=False)
def get_claims_by_provider_type() -> Optional[list[dict[str, Any]]]:
    return _request("GET", "/analytics/by-provider-type")


@st.cache_data(ttl=60, show_spinner=False)
def get_high_amount_claims(limit: int = 20) -> Optional[list[dict[str, Any]]]:
    return _request("GET", "/fraud/high-amount-claims", params={"limit": limit})


@st.cache_data(ttl=60, show_spinner=False)
def get_pipeline_status() -> Optional[dict[str, Any]]:
    return _request("GET", "/pipeline/status")


@st.cache_data(ttl=60, show_spinner=False)
def get_claims(limit: int = 25, offset: int = 0) -> Optional[dict[str, Any]]:
    return _request("GET", "/claims", params={"limit": limit, "offset": offset})


@st.cache_data(ttl=60, show_spinner=False)
def get_claim_by_id(claim_id: int) -> Optional[dict[str, Any]]:
    return _request("GET", f"/claims/{claim_id}")


# ── Non-Cached Dynamic Endpoints (Chat & Investigation) ──

def send_chat_message(
    message: str,
    thread_id: Optional[str] = None,
    history: Optional[list[dict[str, str]]] = None,
) -> Optional[dict[str, Any]]:
    """Send chat message to LLM agent (uncached, 90s timeout)."""
    return _request(
        "POST",
        "/chat",
        json_data={"message": message, "thread_id": thread_id, "history": history},
        timeout=LLM_TIMEOUT,
    )


def run_claim_investigation(claim_id: int) -> Optional[dict[str, Any]]:
    """Run AI fraud investigation on claim (uncached, 90s timeout)."""
    return _request(
        "POST",
        "/investigations",
        json_data={"claim_id": claim_id},
        timeout=LLM_TIMEOUT,
    )

