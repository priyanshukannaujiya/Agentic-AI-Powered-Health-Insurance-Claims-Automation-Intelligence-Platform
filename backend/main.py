"""FastAPI application for Claims Agentic Platform.

Exposes REST endpoints that the Streamlit frontend consumes.
All data comes from Databricks Gold-layer tables via backend.tools.database.
"""

from __future__ import annotations

import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.tools.database import (
    get_claims,
    get_claim_by_id,
    get_analytics_summary,
    get_claims_by_state,
    get_top_providers,
    get_monthly_trend,
    get_claims_by_provider_type,
    get_high_amount_claims,
    get_pipeline_status,
    get_claim_fraud_details,
)
from backend.llm.client import chat as llm_chat, investigate_claim

app = FastAPI(
    title="Claims Agentic Platform API",
    version="1.0.0",
    description="AI-powered health insurance claims automation & intelligence",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    history: Optional[list[dict]] = None


class InvestigationRequest(BaseModel):
    claim_id: int


# ── Health ─────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "claims-agentic-platform"}


# ── Claims ─────────────────────────────────────────────

@app.get("/claims")
def list_claims(
    limit: int = Query(25, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    try:
        return get_claims(limit=limit, offset=offset)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/claims/{claim_id}")
def get_single_claim(claim_id: int):
    try:
        claim = get_claim_by_id(claim_id)
        if not claim:
            raise HTTPException(status_code=404, detail=f"Claim {claim_id} not found")
        return claim
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Analytics ──────────────────────────────────────────

@app.get("/analytics")
def analytics_summary():
    try:
        return get_analytics_summary()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/by-state")
def analytics_by_state(limit: int = Query(50, ge=1, le=50)):
    try:
        return get_claims_by_state(limit=limit)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/top-providers")
def analytics_top_providers(limit: int = Query(20, ge=1, le=50)):
    try:
        return get_top_providers(limit=limit)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/monthly-trend")
def analytics_monthly_trend(year: Optional[int] = None):
    try:
        return get_monthly_trend(year=year)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/by-provider-type")
def analytics_by_provider_type():
    try:
        return get_claims_by_provider_type()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Fraud ──────────────────────────────────────────────

@app.get("/fraud/high-amount-claims")
def fraud_high_amount_claims(limit: int = Query(20, ge=1, le=50)):
    try:
        return get_high_amount_claims(limit=limit)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Pipeline ──────────────────────────────────────────

@app.get("/pipeline/status")
def pipeline_status():
    try:
        return get_pipeline_status()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Chat ──────────────────────────────────────────────

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    try:
        result = llm_chat(
            message=req.message,
            history=req.history,
            thread_id=req.thread_id,
        )
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Investigations ────────────────────────────────────

@app.post("/investigations")
def run_investigation(req: InvestigationRequest):
    try:
        fraud_details = get_claim_fraud_details(req.claim_id)
        if not fraud_details:
            raise HTTPException(
                status_code=404, detail=f"Claim {req.claim_id} not found"
            )
        result = investigate_claim(
            claim_data=fraud_details["claim"],
            fraud_details=fraud_details,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

