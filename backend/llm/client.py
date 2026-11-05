"""LLM client implementation.

Uses Groq SDK to power the AI chat agent.
Keeps model interaction code isolated so providers can be swapped.
"""

from __future__ import annotations

from groq import Groq

from backend.config import settings

# System prompt that scopes the agent to claims data
SYSTEM_PROMPT = """You are an AI assistant for a Health Insurance Claims Intelligence Platform.
You help analysts understand claims data, identify potential fraud patterns, and summarise claim portfolios.

IMPORTANT RULES:
- This platform operates on BATCH-PROCESSED enterprise claims data ingested via scheduled Azure Data Factory ETL pipelines into the Databricks Lakehouse Gold layer.
- You are read-only: you cannot approve, reject, or modify any claim.
- Risk indicators are decision-support signals and require human review.
- Be concise, use bullet points and tables where helpful.
- When discussing monetary amounts, use $ with comma separators.
- If asked about something outside health insurance claims, politely redirect."""

INVESTIGATION_PROMPT = """You are a fraud investigation analyst AI.
Given the batch-processed claim data and risk signals below, produce a structured investigation summary:

1. **Risk Level**: Assess as LOW, MEDIUM, or HIGH based on the signals.
2. **Key Risk Signals**: List each signal with its value and why it matters.
3. **Investigation Summary**: A 3-5 sentence narrative of the findings.
4. **Recommended Actions**: What a human reviewer should check next.

IMPORTANT: All findings are decision-support risk indicators requiring human audit review.
Risk indicators are not definitive proof of fraud."""


def chat(message: str, history: list[dict] | None = None,
         thread_id: str | None = None) -> dict:
    """Send a message to the LLM with optional conversation history.

    Returns {"response": str, "agents_used": list[str], "thread_id": str}.
    """
    client = Groq(api_key=settings.groq_api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.3,
        max_tokens=2048,
    )

    response_text = completion.choices[0].message.content or ""
    agents_used = ["Claims Analyst Agent"]

    if any(kw in message.lower() for kw in ["fraud", "risk", "suspicious", "investigate"]):
        agents_used.append("Fraud Detection Agent")
    if any(kw in message.lower() for kw in ["trend", "analytic", "summary", "overview", "portfolio"]):
        agents_used.append("Analytics Agent")

    return {
        "response": response_text.strip(),
        "agents_used": agents_used,
        "thread_id": thread_id or "default",
    }


def investigate_claim(claim_data: dict, fraud_details: dict) -> dict:
    """Run an AI-powered fraud investigation on a single claim.

    Returns {"risk_level": str, "risk_signals": list, "summary": str, "agents_used": list}.
    """
    claim = fraud_details.get("claim", claim_data)
    ratio = fraud_details.get("amount_vs_provider_avg_ratio")
    provider_avg = fraud_details.get("provider_avg_amount", 0)

    # Build risk signals
    signals = []
    amount = claim.get("Claim_Amount", 0)
    if ratio and ratio > 3:
        signals.append({"signal": "Amount vs Provider Average", "value": f"{ratio}x",
                        "severity": "HIGH"})
    elif ratio and ratio > 1.5:
        signals.append({"signal": "Amount vs Provider Average", "value": f"{ratio}x",
                        "severity": "MEDIUM"})
    else:
        signals.append({"signal": "Amount vs Provider Average", "value": f"{ratio}x" if ratio else "N/A",
                        "severity": "LOW"})

    if claim.get("Claim_Submitted_Late"):
        signals.append({"signal": "Late Submission", "value": "Yes",
                        "severity": "MEDIUM"})

    prev_patient = claim.get("Number_of_Previous_Claims_Patient", 0)
    if prev_patient and prev_patient > 10:
        signals.append({"signal": "Previous Patient Claims", "value": str(prev_patient),
                        "severity": "MEDIUM"})

    prev_provider = claim.get("Number_of_Previous_Claims_Provider", 0)
    if prev_provider and prev_provider > 20:
        signals.append({"signal": "High Provider Claim Volume", "value": str(prev_provider),
                        "severity": "MEDIUM"})

    los = claim.get("Length_of_Stay_Days", 0)
    if los and los > 30:
        signals.append({"signal": "Extended Length of Stay", "value": f"{los} days",
                        "severity": "MEDIUM"})

    if amount > 1_000_000:
        signals.append({"signal": "Very High Claim Amount", "value": f"${amount:,.2f}",
                        "severity": "HIGH"})

    # Determine overall risk
    high_count = sum(1 for s in signals if s["severity"] == "HIGH")
    med_count = sum(1 for s in signals if s["severity"] == "MEDIUM")
    if high_count >= 2 or (high_count >= 1 and med_count >= 2):
        risk_level = "HIGH"
    elif high_count >= 1 or med_count >= 2:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Generate AI narrative
    context = (
        f"Claim ID: {claim.get('Claim_ID')}\n"
        f"Amount: ${amount:,.2f}\n"
        f"Provider Average: ${provider_avg:,.2f}\n"
        f"Amount/Provider Avg Ratio: {ratio}\n"
        f"Late Submission: {claim.get('Claim_Submitted_Late')}\n"
        f"Previous Patient Claims: {prev_patient}\n"
        f"Previous Provider Claims: {prev_provider}\n"
        f"Length of Stay: {los} days\n"
        f"Provider Type: {claim.get('Provider_Type')}\n"
        f"Provider Specialty: {claim.get('Provider_Specialty')}\n"
        f"Is_Fraudulent flag: {claim.get('Is_Fraudulent')}\n"
        f"Risk Signals: {signals}\n"
    )

    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": INVESTIGATION_PROMPT},
            {"role": "user", "content": context},
        ],
        temperature=0.2,
        max_tokens=1500,
    )
    summary = (completion.choices[0].message.content or "").strip()

    return {
        "claim_id": claim.get("Claim_ID"),
        "risk_level": risk_level,
        "risk_signals": signals,
        "summary": summary,
        "provider_avg_amount": provider_avg,
        "amount_vs_provider_avg_ratio": ratio,
        "agents_used": ["Claims Analyst Agent", "Fraud Detection Agent"],
    }
