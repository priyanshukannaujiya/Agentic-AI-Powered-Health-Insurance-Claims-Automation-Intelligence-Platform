"""Read-only database tools for Azure Databricks claims platform.

Provides functions that query the Gold-layer star schema
(fact_claims, dim_member, dim_provider, dim_diagnosis, dim_date).
Every function returns plain Python dicts/lists suitable for JSON serialization.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from typing import Any

from databricks.sql import connect
from databricks.sql.client import Connection

from backend.config import settings


@contextmanager
def get_connection() -> Connection:
    """Yield a short-lived Databricks SQL connection."""
    conn = connect(
        server_hostname=settings.databricks_server_hostname,
        http_path=settings.databricks_http_path,
        access_token=settings.databricks_token,
    )
    try:
        yield conn
    finally:
        conn.close()


def _rows_to_dicts(cursor) -> list[dict[str, Any]]:
    """Convert cursor results to a list of dicts with JSON-safe values."""
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    result = []
    for row in rows:
        d = {}
        for col, val in zip(columns, row):
            if isinstance(val, (date, datetime)):
                d[col] = val.isoformat()
            else:
                d[col] = val
        result.append(d)
    return result


# ──────────────────────────────────────────────
#  Claims queries
# ──────────────────────────────────────────────

def get_claims(limit: int = 25, offset: int = 0) -> dict:
    """Return paginated claims joined with member and provider info."""
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM default.fact_claims")
        total = cur.fetchone()[0]

        cur.execute(f"""
            SELECT
                fc.Claim_ID, fc.Claim_Date, fc.Service_Date,
                fc.Claim_Amount, fc.Deductible_Amount, fc.CoPay_Amount,
                fc.Number_of_Procedures, fc.Length_of_Stay_Days,
                fc.Claim_Submitted_Late, fc.Is_Fraudulent,
                fc.Diagnosis_Code, fc.Procedure_Code,
                dm.Patient_ID, dm.Patient_Age, dm.Patient_Gender,
                dm.Patient_City, dm.Patient_State, dm.Policy_Number,
                dp.Hospital_ID, dp.Provider_Type, dp.Provider_Specialty,
                dp.Provider_City, dp.Provider_State
            FROM default.fact_claims fc
            LEFT JOIN default.dim_member dm ON fc.Patient_ID = dm.Patient_ID
            LEFT JOIN default.dim_provider dp ON fc.Hospital_ID = dp.Hospital_ID
            ORDER BY fc.Claim_ID
            LIMIT {int(limit)} OFFSET {int(offset)}
        """)
        claims = _rows_to_dicts(cur)
        cur.close()

    return {"total": total, "limit": limit, "offset": offset, "claims": claims}


def get_claim_by_id(claim_id: int) -> dict | None:
    """Return a single claim with full details, or None."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                fc.Claim_ID, fc.Claim_Date, fc.Service_Date,
                fc.Claim_Amount, fc.Deductible_Amount, fc.CoPay_Amount,
                fc.Number_of_Procedures, fc.Length_of_Stay_Days,
                fc.Claim_Submitted_Late, fc.Is_Fraudulent,
                fc.Diagnosis_Code, fc.Procedure_Code,
                fc.Number_of_Previous_Claims_Patient,
                fc.Number_of_Previous_Claims_Provider,
                dm.Patient_ID, dm.Patient_Age, dm.Patient_Gender,
                dm.Patient_City, dm.Patient_State, dm.Policy_Number,
                dp.Hospital_ID, dp.Provider_Type, dp.Provider_Specialty,
                dp.Provider_City, dp.Provider_State,
                dd.Admission_Type, dd.Discharge_Type, dd.Service_Type
            FROM default.fact_claims fc
            LEFT JOIN default.dim_member dm ON fc.Patient_ID = dm.Patient_ID
            LEFT JOIN default.dim_provider dp ON fc.Hospital_ID = dp.Hospital_ID
            LEFT JOIN default.dim_diagnosis dd
                ON fc.Diagnosis_Code = dd.Diagnosis_Code
                AND fc.Procedure_Code = dd.Procedure_Code
            WHERE fc.Claim_ID = {int(claim_id)}
            LIMIT 1
        """)
        rows = _rows_to_dicts(cur)
        cur.close()

    return rows[0] if rows else None


# ──────────────────────────────────────────────
#  Analytics queries
# ──────────────────────────────────────────────

def get_analytics_summary() -> dict:
    """High-level KPI metrics."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*)                        AS total_claims,
                COUNT(DISTINCT Patient_ID)      AS distinct_patients,
                SUM(Claim_Amount)               AS total_claim_amount,
                AVG(Claim_Amount)               AS avg_claim_amount,
                SUM(CASE WHEN Is_Fraudulent THEN 1 ELSE 0 END) AS flagged_claims,
                AVG(Length_of_Stay_Days)         AS avg_length_of_stay
            FROM default.fact_claims
        """)
        row = _rows_to_dicts(cur)[0]
        cur.close()
    return row


def get_claims_by_state(limit: int = 50) -> list[dict]:
    """Claims count and total amount grouped by patient state."""
    limit = min(int(limit), 50)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                dm.Patient_State AS state,
                COUNT(*)         AS claim_count,
                SUM(fc.Claim_Amount) AS total_amount
            FROM default.fact_claims fc
            JOIN default.dim_member dm ON fc.Patient_ID = dm.Patient_ID
            GROUP BY dm.Patient_State
            ORDER BY claim_count DESC
            LIMIT {limit}
        """)
        data = _rows_to_dicts(cur)
        cur.close()
    return data


def get_top_providers(limit: int = 20) -> list[dict]:
    """Top providers by claim count."""
    limit = min(int(limit), 50)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                dp.Hospital_ID,
                dp.Provider_Type,
                dp.Provider_Specialty,
                dp.Provider_City,
                dp.Provider_State,
                COUNT(*)             AS claim_count,
                SUM(fc.Claim_Amount) AS total_amount,
                AVG(fc.Claim_Amount) AS avg_amount
            FROM default.fact_claims fc
            JOIN default.dim_provider dp ON fc.Hospital_ID = dp.Hospital_ID
            GROUP BY dp.Hospital_ID, dp.Provider_Type, dp.Provider_Specialty,
                     dp.Provider_City, dp.Provider_State
            ORDER BY claim_count DESC
            LIMIT {limit}
        """)
        data = _rows_to_dicts(cur)
        cur.close()
    return data


def get_monthly_trend(year: int | None = None) -> list[dict]:
    """Monthly claims trend. Optionally filter by year."""
    where = f"WHERE dd.year = {int(year)}" if year else ""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                dd.year,
                dd.month,
                COUNT(*)             AS claim_count,
                SUM(fc.Claim_Amount) AS total_amount
            FROM default.fact_claims fc
            JOIN default.dim_date dd ON fc.Claim_Date = dd.full_date
            {where}
            GROUP BY dd.year, dd.month
            ORDER BY dd.year, dd.month
        """)
        data = _rows_to_dicts(cur)
        cur.close()
    return data


def get_claims_by_provider_type() -> list[dict]:
    """Claims grouped by provider type."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                dp.Provider_Type      AS provider_type,
                COUNT(*)              AS claim_count,
                SUM(fc.Claim_Amount)  AS total_amount,
                AVG(fc.Claim_Amount)  AS avg_amount
            FROM default.fact_claims fc
            JOIN default.dim_provider dp ON fc.Hospital_ID = dp.Hospital_ID
            GROUP BY dp.Provider_Type
            ORDER BY claim_count DESC
        """)
        data = _rows_to_dicts(cur)
        cur.close()
    return data


def get_high_amount_claims(limit: int = 20) -> list[dict]:
    """Top claims by dollar amount (potential fraud signals)."""
    limit = min(int(limit), 50)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT
                fc.Claim_ID, fc.Claim_Amount, fc.Claim_Date,
                fc.Is_Fraudulent, fc.Claim_Submitted_Late,
                fc.Number_of_Procedures, fc.Length_of_Stay_Days,
                dm.Patient_State,
                dp.Provider_Type, dp.Provider_Specialty
            FROM default.fact_claims fc
            LEFT JOIN default.dim_member dm ON fc.Patient_ID = dm.Patient_ID
            LEFT JOIN default.dim_provider dp ON fc.Hospital_ID = dp.Hospital_ID
            ORDER BY fc.Claim_Amount DESC
            LIMIT {limit}
        """)
        data = _rows_to_dicts(cur)
        cur.close()
    return data


def get_pipeline_status() -> dict:
    """Row counts for the five Gold tables plus a timestamp."""
    tables = ["fact_claims", "dim_member", "dim_provider", "dim_diagnosis", "dim_date"]
    counts = {}
    with get_connection() as conn:
        cur = conn.cursor()
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM default.{t}")
            counts[t] = cur.fetchone()[0]
        cur.close()
    return {
        "table_counts": counts,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_claim_fraud_details(claim_id: int) -> dict | None:
    """Gather data needed for fraud investigation of a specific claim."""
    claim = get_claim_by_id(claim_id)
    if not claim:
        return None

    with get_connection() as conn:
        cur = conn.cursor()
        # Provider average for comparison
        cur.execute(f"""
            SELECT AVG(Claim_Amount) AS provider_avg
            FROM default.fact_claims
            WHERE Hospital_ID = (
                SELECT Hospital_ID FROM default.fact_claims
                WHERE Claim_ID = {int(claim_id)} LIMIT 1
            )
        """)
        provider_avg = cur.fetchone()[0] or 0
        cur.close()

    ratio = round(claim["Claim_Amount"] / provider_avg, 2) if provider_avg else None

    return {
        "claim": claim,
        "provider_avg_amount": round(provider_avg, 2),
        "amount_vs_provider_avg_ratio": ratio,
    }
