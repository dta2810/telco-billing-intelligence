"""FastAPI routes for AcmeTel Billing Intelligence.

This module is grown sprint-by-sprint. Initial scaffold has health + a smoke
test endpoint that proves the DB connection + Genie space are reachable.
Full route map (target):

GET  /api/health                            health + env summary
GET  /api/exec/kpis                         6 KPI tiles (executive)
GET  /api/exec/insights                     ai_query polished insights
GET  /api/customer/kpis                     5 KPI tiles (customer page top)
GET  /api/customer/list                     filterable customer list with state flags
GET  /api/customer/{id}/profile             header profile + 3 status chips (auto UC fns)
GET  /api/customer/{id}/invoices            6-month invoice trail + breakdown
POST /api/customer/{id}/action/{tool}       invoke UC function
POST /api/genie/chat                        Genie passthrough (optional customer scope)
POST /api/agent/chat                        Supervisor: routes Genie ↔ UC fn + ai_query polish
"""
import json
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.db import execute_query, execute_queries_parallel, CATALOG, SCHEMA, _get_workspace_client
from server import i18n

logger = logging.getLogger(__name__)


def _fn(lang: Any, name: str) -> str:
    """UC function name. Functions already emit English, so no per-language variant."""
    return name


# ----------------------------------------------------------------------------
# Pydantic models
# ----------------------------------------------------------------------------

class GenieMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AgentChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    customer_id: Optional[str] = None  # used in /customer page later
    lang: Optional[str] = "es"


class MemoryChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None   # session; echo back to keep short-term continuity
    customer_id: Optional[str] = None  # scope → seeds the subscriber's long-term memory
    lang: Optional[str] = "es"

router = APIRouter()

GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "01f1a591f61715668706a3321c36900e")

# The customer-360 chat is powered by the embedded memory agent (in-process, no HTTP hop).


# ----------------------------------------------------------------------------
# Health / smoke
# ----------------------------------------------------------------------------

@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "catalog": CATALOG,
        "schema": SCHEMA,
        "genie_space_id": GENIE_SPACE_ID,
        "is_databricks_app": bool(os.environ.get("DATABRICKS_APP_NAME")),
    }


@router.get("/smoke")
def smoke() -> dict[str, Any]:
    """Validate end-to-end: catalog reachable, 10 tables loaded, UC fn executes."""
    counts = execute_query(f"""
        SELECT 'customer' AS t, COUNT(*) AS n FROM {CATALOG}.{SCHEMA}.customer UNION ALL
        SELECT 'subscription', COUNT(*) FROM {CATALOG}.{SCHEMA}.subscription UNION ALL
        SELECT 'invoice', COUNT(*) FROM {CATALOG}.{SCHEMA}.invoice UNION ALL
        SELECT 'payment', COUNT(*) FROM {CATALOG}.{SCHEMA}.payment
    """)
    fn_test = execute_query(
        f"SELECT * FROM {CATALOG}.{SCHEMA}.check_discount_status('CUS-000002')"
    )
    arpu = execute_query(f"""
        SELECT MEASURE(arpu) AS arpu, MEASURE(total_revenue) AS revenue
        FROM {CATALOG}.{SCHEMA}.mv_arpu_monthly
        WHERE billing_period = (SELECT MAX(billing_period) FROM {CATALOG}.{SCHEMA}.invoice)
    """)
    return {
        "table_counts": {r["t"]: r["n"] for r in counts},
        "uc_function_check_discount_status": fn_test[0] if fn_test else None,
        "metric_view_arpu_last_period": arpu[0] if arpu else None,
    }


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


_LAST_PERIOD_CACHE: dict[str, Any] = {"value": None, "until": 0.0}


def _last_period() -> str:
    """Return the most recent billing_period present in invoices (YYYY-MM).

    Cached 5 minutes — this value only changes when a new billing cycle closes,
    and saving 1 query per /exec/* call materially helps page load.
    """
    import time
    now = time.time()
    if _LAST_PERIOD_CACHE["value"] and now < _LAST_PERIOD_CACHE["until"]:
        return _LAST_PERIOD_CACHE["value"]
    rows = execute_query(f"SELECT MAX(billing_period) AS p FROM {CATALOG}.{SCHEMA}.invoice")
    period = rows[0]["p"] if rows else ""
    _LAST_PERIOD_CACHE["value"] = period
    _LAST_PERIOD_CACHE["until"] = now + 300
    return period


# ----------------------------------------------------------------------------
# Executive view
# ----------------------------------------------------------------------------

def _exec_kpi_queries(period: str) -> list[str]:
    """The 8 queries that power the executive KPI tiles.
    Order is contract — `_build_kpi_tiles` unpacks results positionally."""
    return [
        # arpu (current period)
        f"""SELECT MEASURE(arpu) AS arpu,
                   MEASURE(total_revenue) AS revenue,
                   MEASURE(customers_billed) AS customers
            FROM {CATALOG}.{SCHEMA}.mv_arpu_monthly
            WHERE billing_period = '{period}'""",
        # arpu_prev
        f"""SELECT MEASURE(arpu) AS arpu
            FROM {CATALOG}.{SCHEMA}.mv_arpu_monthly
            WHERE billing_period = (
              SELECT MAX(billing_period) FROM {CATALOG}.{SCHEMA}.invoice
              WHERE billing_period < '{period}'
            )""",
        # coll
        f"""SELECT MEASURE(collection_rate) AS rate,
                   MEASURE(paid_invoices) AS paid,
                   MEASURE(total_invoices) AS total
            FROM {CATALOG}.{SCHEMA}.mv_collection_rate
            WHERE billing_period = '{period}'""",
        # rar
        f"""SELECT MEASURE(revenue_at_risk) AS rev,
                   MEASURE(customers_at_risk) AS custs
            FROM {CATALOG}.{SCHEMA}.mv_revenue_at_risk""",
        # disc
        f"""SELECT MEASURE(at_risk_count) AS clientes,
                   MEASURE(subscriptions_count) AS subs
            FROM {CATALOG}.{SCHEMA}.mv_discount_expiring_30d""",
        # contracts
        f"""SELECT MEASURE(contracts_count) AS n,
                   MEASURE(total_etf) AS etf
            FROM {CATALOG}.{SCHEMA}.mv_contract_expiring_60d""",
        # overage
        f"""SELECT MEASURE(overage_rate) AS rate,
                   MEASURE(subs_with_overage) AS subs
            FROM {CATALOG}.{SCHEMA}.mv_overage_frequency
            WHERE billing_period = '{period}'""",
        # renewal: recurring revenue tied to contracts ending in 60d
        f"""SELECT COUNT(DISTINCT ct.customer_id) AS customers,
                   SUM(rp.monthly_fee) * 12 AS annual_recurring
            FROM {CATALOG}.{SCHEMA}.contract ct
            JOIN {CATALOG}.{SCHEMA}.subscription s ON ct.subscription_id = s.subscription_id
            JOIN {CATALOG}.{SCHEMA}.rate_plan rp ON s.plan_id = rp.plan_id
            WHERE ct.status = 'active'
              AND ct.end_date BETWEEN current_date() AND date_add(current_date(), 60)""",
    ]


def _build_kpi_tiles(kpi_results: list[list[dict]], lang: Any = "es") -> list[dict]:
    """Turn the 8 raw kpi result sets into the tile payload."""
    arpu, arpu_prev, coll, rar, disc, contracts, overage, renewal = kpi_results

    a = arpu[0] if arpu else {}
    a_prev = arpu_prev[0] if arpu_prev else {}
    c = coll[0] if coll else {}
    r = rar[0] if rar else {}
    d = disc[0] if disc else {}
    ct = contracts[0] if contracts else {}
    o = overage[0] if overage else {}
    rn = renewal[0] if renewal else {}

    arpu_now = _safe_float(a.get("arpu"))
    arpu_old = _safe_float(a_prev.get("arpu"))
    arpu_delta = arpu_now - arpu_old if arpu_old else 0.0

    return [
        {
            "id": "arpu",
            "label": i18n.tr(lang, "exec.arpu.label"),
            "value": arpu_now,
            "format": "currency",
            "trend": arpu_delta,
            "subtitle": i18n.tr(lang, "exec.arpu.subtitle", n=_safe_int(a.get("customers"))),
            "tone": "neutral",
        },
        {
            "id": "collection_rate",
            "label": i18n.tr(lang, "exec.collection.label"),
            "value": _safe_float(c.get("rate")) * 100,
            "format": "percent",
            "subtitle": i18n.tr(lang, "exec.collection.subtitle",
                                paid=_safe_int(c.get("paid")), total=_safe_int(c.get("total"))),
            "tone": "good" if _safe_float(c.get("rate")) >= 0.9 else "warn",
        },
        {
            "id": "revenue_at_risk",
            "label": i18n.tr(lang, "exec.rar.label"),
            "value": _safe_float(r.get("rev")),
            "format": "currency",
            "subtitle": i18n.tr(lang, "exec.rar.subtitle", n=_safe_int(r.get("custs"))),
            "tone": "alert" if _safe_float(r.get("rev")) > 500 else "warn",
        },
        {
            "id": "discounts_expiring",
            "label": i18n.tr(lang, "exec.disc.label"),
            "value": _safe_int(d.get("clientes")),
            "format": "count",
            "subtitle": i18n.tr(lang, "exec.disc.subtitle", n=_safe_int(d.get("subs"))),
            "tone": "warn",
        },
        {
            "id": "contracts_expiring",
            "label": i18n.tr(lang, "exec.contracts.label"),
            "value": _safe_int(ct.get("n")),
            "format": "count",
            "subtitle": i18n.tr(lang, "exec.contracts.subtitle",
                                n=_safe_int(rn.get("customers")),
                                arr=f"{_safe_float(rn.get('annual_recurring')):,.0f}"),
            "tone": "warn",
        },
        {
            "id": "overage_rate",
            "label": i18n.tr(lang, "exec.overage.label"),
            "value": _safe_float(o.get("rate")) * 100,
            "format": "percent",
            "subtitle": i18n.tr(lang, "exec.overage.subtitle", n=_safe_int(o.get("subs"))),
            "tone": "neutral",
        },
    ]


def _exec_insights_queries(period: str) -> list[str]:
    """The 3 supplementary queries for /exec/insights (after the kpi block)."""
    return [
        # dunning distribution
        f"""SELECT dunning_stage,
                   MEASURE(payments_count) AS pagos,
                   MEASURE(customers_count) AS clientes
            FROM {CATALOG}.{SCHEMA}.mv_dunning_distribution
            GROUP BY dunning_stage ORDER BY dunning_stage""",
        # arpu trend
        f"""SELECT billing_period, MEASURE(arpu) AS arpu, MEASURE(total_revenue) AS revenue
            FROM {CATALOG}.{SCHEMA}.mv_arpu_monthly
            GROUP BY billing_period ORDER BY billing_period""",
        # overage by plan
        f"""SELECT plan_name, MEASURE(overage_rate) AS rate, MEASURE(subs_with_overage) AS subs
            FROM {CATALOG}.{SCHEMA}.mv_overage_frequency
            WHERE billing_period = '{period}'
            GROUP BY plan_name ORDER BY rate DESC""",
        # revenue by charge type, current vs previous period (explains ARPU moves)
        f"""SELECT i.billing_period, il.charge_type, ROUND(SUM(il.amount), 2) AS amount
            FROM {CATALOG}.{SCHEMA}.invoice_line il
            JOIN {CATALOG}.{SCHEMA}.invoice i ON il.invoice_id = i.invoice_id
            WHERE i.billing_period IN ('{period}', (
              SELECT MAX(billing_period) FROM {CATALOG}.{SCHEMA}.invoice WHERE billing_period < '{period}'))
            GROUP BY i.billing_period, il.charge_type ORDER BY il.charge_type, i.billing_period""",
        # bill shock: customers whose discount expired in the last 60 days and their monthly bill increase
        f"""WITH cohort AS (
              SELECT DISTINCT s.customer_id
              FROM {CATALOG}.{SCHEMA}.subscription_promotion sp
              JOIN {CATALOG}.{SCHEMA}.subscription s ON sp.subscription_id = s.subscription_id
              WHERE sp.status = 'expired'
                AND sp.end_date BETWEEN date_sub(current_date(), 60) AND date_sub(current_date(), 1)
            ),
            per_cust AS (
              SELECT i.customer_id,
                     MAX(CASE WHEN i.billing_period < '{period}' THEN i.discount_amount END)
                       - MAX(CASE WHEN i.billing_period = '{period}' THEN i.discount_amount END) AS increase
              FROM {CATALOG}.{SCHEMA}.invoice i
              JOIN cohort c ON i.customer_id = c.customer_id
              WHERE i.billing_period >= date_format(add_months(to_date('{period}-01'), -3), 'yyyy-MM')
              GROUP BY i.customer_id
            )
            SELECT COUNT(*) AS customers,
                   SUM(CASE WHEN increase > 0 THEN 1 ELSE 0 END) AS customers_with_higher_bill,
                   ROUND(AVG(CASE WHEN increase > 0 THEN increase END), 2) AS avg_monthly_bill_increase,
                   ROUND(SUM(CASE WHEN increase > 0 THEN increase END), 2) AS total_monthly_bill_increase
            FROM per_cust""",
    ]


@router.get("/exec/kpis")
def exec_kpis(lang: str = "es") -> dict[str, Any]:
    """Six KPI tiles powered by the metric views from Sprint 1."""
    period = _last_period()
    results = execute_queries_parallel(_exec_kpi_queries(period))
    return {"period": period, "tiles": _build_kpi_tiles(results, lang)}


@router.get("/exec/insights")
def exec_insights(lang: str = "es") -> dict[str, Any]:
    """Structured signals + AI-polished executive brief."""
    period = _last_period()

    # All KPI + insight queries in one parallel batch instead of two serial waves.
    all_queries = _exec_kpi_queries(period) + _exec_insights_queries(period)
    results = execute_queries_parallel(all_queries)
    kpi_results = results[:8]
    dunning, arpu_trend, overage_by_plan, revenue_by_charge, bill_shock = results[8:]

    tiles_list = _build_kpi_tiles(kpi_results, lang)
    tiles = {t["id"]: t for t in tiles_list}

    # Convert Decimals -> floats for JSON / prompt assembly
    def clean(rows):
        return [
            {k: (_safe_float(v) if v is not None and not isinstance(v, str) else v)
             for k, v in row.items()}
            for row in rows
        ]

    structured = {
        "period": period,
        "kpis": {tid: {k: t[k] for k in ("value", "subtitle", "tone")} for tid, t in tiles.items()},
        "dunning_distribution": clean(dunning),
        "arpu_trend": clean(arpu_trend),
        "overage_by_plan": clean(overage_by_plan),
        "revenue_by_charge_type": clean(revenue_by_charge),
        "expired_discount_bill_shock": clean(bill_shock),
        "definitions": {
            "collection_rate": "share of THIS period's invoices already paid",
            "revenue_at_risk": "cumulative unpaid balance (several periods) of customers 61+ days overdue",
            "contracts_expiring": "contracts whose commitment ends in 60 days: the risk is non-renewal "
                                  "(annual recurring revenue at stake), not the early-termination fee, "
                                  "which no longer applies once the contract ends",
            "one_time_charges": "device sales and activation fees; volatile, not recurring revenue",
            "expired_discount_bill_shock": "customers whose discount expired in the last 60 days and how much "
                                           "their monthly bill rose; they are the ones calling 'why did my bill "
                                           "go up?' and the main retention opportunity",
        },
    }

    # AI-polished narrative
    summary_text = json.dumps(structured, ensure_ascii=False, indent=2)
    prompt = i18n.build_insights_prompt(lang, period, summary_text)
    safe_prompt = prompt.replace("'", "''")
    try:
        ai = execute_query(
            f"SELECT ai_query('databricks-claude-sonnet-4-5', '{safe_prompt}') AS result"
        )
        narrative = ai[0]["result"] if ai else i18n.tr(lang, "narrative.unavailable")
    except Exception as e:
        logger.exception("ai_query failed")
        narrative = i18n.tr(lang, "narrative.unavailable_err", e=type(e).__name__)

    return {
        "period": period,
        "narrative": narrative,
        "structured": structured,
    }


# ----------------------------------------------------------------------------
# Genie Chat (raw passthrough)
# ----------------------------------------------------------------------------

def _extract_genie_response(msg, w) -> dict[str, Any]:
    """Pull text + SQL + first 20 rows from a Genie message envelope."""
    text_parts: list[str] = []
    genie_query: Optional[str] = None
    query_result: Optional[dict[str, Any]] = None

    if msg.attachments:
        for att in msg.attachments:
            if att.text and att.text.content:
                text_parts.append(att.text.content)
            if att.query and att.query.query:
                genie_query = att.query.query
                if hasattr(msg, "query_result") and msg.query_result:
                    try:
                        stmt = w.statement_execution.get_statement(
                            msg.query_result.statement_id
                        )
                        if stmt.result and stmt.result.data_array:
                            cols = [c.name for c in stmt.manifest.schema.columns]
                            rows = stmt.result.data_array[:20]
                            # Stringify all cells for safe transport
                            rows = [[("" if c is None else str(c)) for c in r] for r in rows]
                            query_result = {"columns": cols, "rows": rows}
                    except Exception as qe:
                        logger.warning(f"Could not fetch query result: {qe}")

    return {
        "text": "\n\n".join(text_parts) if text_parts else "",
        "genie_query": genie_query,
        "query_result": query_result,
    }


@router.post("/genie/chat")
def genie_chat(body: GenieMessageRequest) -> dict[str, Any]:
    """Send a message to the Genie space and return the raw response."""
    try:
        w = _get_workspace_client()
        if body.conversation_id:
            msg = w.genie.create_message_and_wait(
                space_id=GENIE_SPACE_ID,
                conversation_id=body.conversation_id,
                content=body.message,
            )
        else:
            msg = w.genie.start_conversation_and_wait(
                space_id=GENIE_SPACE_ID,
                content=body.message,
            )
        extracted = _extract_genie_response(msg, w)
        return {
            "conversation_id": msg.conversation_id,
            "response": extracted["text"] or "Sin respuesta generada.",
            "genie_query": extracted["genie_query"],
            "query_result": extracted["query_result"],
        }
    except Exception:
        logger.exception("Genie chat error")
        raise HTTPException(status_code=500, detail="Genie chat failed. Please try again.")


# ----------------------------------------------------------------------------
# Supervisor Agent — Genie + ai_query polish
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Customer view (master-detail)
# ----------------------------------------------------------------------------

@router.get("/customer/kpis")
def customer_kpis(lang: str = "es") -> dict[str, Any]:
    """5 KPI tiles for the top of the /customer page."""
    rows = execute_query(f"""
        WITH base AS (
          SELECT c.customer_id, c.segment, c.status FROM {CATALOG}.{SCHEMA}.customer c
        ),
        mora_60 AS (
          SELECT DISTINCT customer_id FROM {CATALOG}.{SCHEMA}.payment WHERE dunning_stage >= 3
        ),
        mora_30 AS (
          SELECT DISTINCT customer_id FROM {CATALOG}.{SCHEMA}.payment WHERE dunning_stage = 1
        ),
        expired_disc AS (
          SELECT DISTINCT s.customer_id
          FROM {CATALOG}.{SCHEMA}.subscription_promotion sp
          JOIN {CATALOG}.{SCHEMA}.subscription s ON sp.subscription_id = s.subscription_id
          WHERE sp.status = 'expired'
            AND sp.end_date BETWEEN date_sub(current_date(), 60) AND date_sub(current_date(), 1)
        ),
        contract_exp AS (
          SELECT DISTINCT customer_id FROM {CATALOG}.{SCHEMA}.contract
          WHERE status = 'active' AND end_date BETWEEN current_date() AND date_add(current_date(), 60)
        ),
        overage AS (
          SELECT DISTINCT s.customer_id
          FROM {CATALOG}.{SCHEMA}.usage_summary u
          JOIN {CATALOG}.{SCHEMA}.subscription s ON u.subscription_id = s.subscription_id
          WHERE u.data_overage_mb > 2048
            AND u.billing_period >= date_format(add_months(current_date(),-3),'yyyy-MM')
        )
        SELECT
          (SELECT COUNT(*) FROM base WHERE status='active') AS total_active,
          (SELECT COUNT(*) FROM mora_60) AS mora_60,
          (SELECT COUNT(*) FROM mora_30) AS mora_30,
          (SELECT COUNT(*) FROM expired_disc) AS expired_discount,
          (SELECT COUNT(*) FROM contract_exp) AS contract_expiring,
          (SELECT COUNT(*) FROM overage) AS with_overage
    """)
    r = rows[0] if rows else {}
    total_active = _safe_int(r.get("total_active"))
    return {
        "tiles": [
            {
                "id": "total_active",
                "label": i18n.tr(lang, "cust.total.label"),
                "value": total_active,
                "format": "count",
                "subtitle": i18n.tr(lang, "cust.total.subtitle"),
                "tone": "neutral",
            },
            {
                "id": "mora_60",
                "label": i18n.tr(lang, "cust.mora60.label"),
                "value": _safe_int(r.get("mora_60")),
                "format": "count",
                "subtitle": i18n.tr(lang, "cust.mora60.subtitle"),
                "tone": "alert",
            },
            {
                "id": "expired_discount",
                "label": i18n.tr(lang, "cust.expdisc.label"),
                "value": _safe_int(r.get("expired_discount")),
                "format": "count",
                "subtitle": i18n.tr(lang, "cust.expdisc.subtitle"),
                "tone": "warn",
            },
            {
                "id": "contract_expiring",
                "label": i18n.tr(lang, "cust.contract.label"),
                "value": _safe_int(r.get("contract_expiring")),
                "format": "count",
                "subtitle": i18n.tr(lang, "cust.contract.subtitle"),
                "tone": "warn",
            },
            {
                "id": "with_overage",
                "label": i18n.tr(lang, "cust.overage.label"),
                "value": _safe_int(r.get("with_overage")),
                "format": "count",
                "subtitle": i18n.tr(lang, "cust.overage.subtitle"),
                "tone": "neutral",
            },
        ]
    }


@router.get("/customer/list")
def customer_list(
    mora_60: bool = False,
    mora_30: bool = False,
    expired_discount: bool = False,
    contract_expiring: bool = False,
    overage: bool = False,
    segment: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Filterable customer list with computed state flags. Each flag maps to one of the
    Outcome Map signals (Churn, Issue Analysis, Contract Buyout, NBO)."""
    base = f"""
      WITH flags AS (
        SELECT
          c.customer_id,
          c.full_name,
          c.segment,
          c.status,
          c.signup_date,
          c.msisdn_primary,
          EXISTS (SELECT 1 FROM {CATALOG}.{SCHEMA}.payment p
                  WHERE p.customer_id = c.customer_id AND p.dunning_stage >= 3) AS f_mora_60,
          EXISTS (SELECT 1 FROM {CATALOG}.{SCHEMA}.payment p
                  WHERE p.customer_id = c.customer_id AND p.dunning_stage = 1) AS f_mora_30,
          EXISTS (
            SELECT 1 FROM {CATALOG}.{SCHEMA}.subscription_promotion sp
            JOIN {CATALOG}.{SCHEMA}.subscription s ON sp.subscription_id = s.subscription_id
            WHERE s.customer_id = c.customer_id AND sp.status = 'expired'
              AND sp.end_date BETWEEN date_sub(current_date(), 60) AND date_sub(current_date(), 1)
          ) AS f_expired_discount,
          EXISTS (
            SELECT 1 FROM {CATALOG}.{SCHEMA}.contract ct
            WHERE ct.customer_id = c.customer_id AND ct.status = 'active'
              AND ct.end_date BETWEEN current_date() AND date_add(current_date(), 60)
          ) AS f_contract_expiring,
          EXISTS (
            SELECT 1 FROM {CATALOG}.{SCHEMA}.usage_summary u
            JOIN {CATALOG}.{SCHEMA}.subscription s ON u.subscription_id = s.subscription_id
            WHERE s.customer_id = c.customer_id AND u.data_overage_mb > 2048
              AND u.billing_period >= date_format(add_months(current_date(),-3),'yyyy-MM')
          ) AS f_overage
        FROM {CATALOG}.{SCHEMA}.customer c
      )
      SELECT * FROM flags
    """
    where: list[str] = []
    if mora_60: where.append("f_mora_60 = TRUE")
    if mora_30: where.append("f_mora_30 = TRUE")
    if expired_discount: where.append("f_expired_discount = TRUE")
    if contract_expiring: where.append("f_contract_expiring = TRUE")
    if overage: where.append("f_overage = TRUE")
    if segment in ("consumer", "smb", "enterprise"):
        where.append(f"segment = '{segment}'")
    if search:
        # Case-insensitive match on customer_id, full_name, or phone number (MSISDN).
        s = search.replace("'", "''")
        where.append(
            f"(LOWER(customer_id) LIKE LOWER('%{s}%') OR LOWER(full_name) LIKE LOWER('%{s}%') "
            f"OR msisdn_primary LIKE '%{s}%')"
        )
    if where:
        base = base + " WHERE " + " AND ".join(where)
    base += f" ORDER BY (CAST(f_mora_60 AS INT) + CAST(f_expired_discount AS INT) + CAST(f_contract_expiring AS INT)) DESC, customer_id ASC LIMIT {int(limit)}"

    rows = execute_query(base)
    # Cast booleans
    for r in rows:
        for k in ("f_mora_60", "f_mora_30", "f_expired_discount", "f_contract_expiring", "f_overage"):
            r[k] = bool(r.get(k))
        # Count active alerts for sort badge
        r["alert_count"] = sum([r["f_mora_60"], r["f_expired_discount"], r["f_contract_expiring"]])

    return {"count": len(rows), "rows": rows}


@router.get("/customer/{customer_id}/profile")
def customer_profile(customer_id: str, lang: str = "es") -> dict[str, Any]:
    """Header info + 3 status chips coming from UC functions."""
    if not customer_id.startswith("CUS-"):
        raise HTTPException(status_code=400, detail="customer_id must start with CUS-")
    cid = customer_id.replace("'", "''")

    header_q = f"""
        SELECT c.customer_id, c.full_name, c.segment, c.status, c.signup_date,
               c.email, c.msisdn_primary,
               (SELECT COUNT(*) FROM {CATALOG}.{SCHEMA}.subscription s
                WHERE s.customer_id = c.customer_id AND s.status='active') AS active_subscriptions
        FROM {CATALOG}.{SCHEMA}.customer c WHERE c.customer_id = '{cid}'
    """
    discount_q = f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'check_discount_status')}('{cid}')"
    payment_q  = f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'get_payment_status')}('{cid}')"
    nbo_q      = f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'get_next_best_offer')}('{cid}')"

    header, discount, payment, nbo = execute_queries_parallel([header_q, discount_q, payment_q, nbo_q])

    if not header:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return {
        "header": header[0],
        "discount_status": discount[0] if discount else None,
        "payment_status": payment[0] if payment else None,
        "next_best_offer": nbo[0] if nbo else None,
    }


@router.get("/customer/{customer_id}/invoices")
def customer_invoices(customer_id: str) -> dict[str, Any]:
    """6-month invoice trail with charge_type breakdown for the Resumen tab."""
    if not customer_id.startswith("CUS-"):
        raise HTTPException(status_code=400, detail="customer_id must start with CUS-")
    cid = customer_id.replace("'", "''")

    trail_q = f"""
        SELECT i.invoice_id, i.billing_period, i.issue_date, i.due_date,
               i.subtotal, i.discount_amount, i.tax_amount, i.total_due, i.status,
               SUM(CASE WHEN il.charge_type = 'recurring'      THEN il.amount END) AS recurring,
               SUM(CASE WHEN il.charge_type = 'discount'       THEN il.amount END) AS discount,
               SUM(CASE WHEN il.charge_type = 'usage_overage'  THEN il.amount END) AS overage,
               SUM(CASE WHEN il.charge_type = 'device_subsidy' THEN il.amount END) AS device_subsidy,
               SUM(CASE WHEN il.charge_type = 'tax'            THEN il.amount END) AS tax
        FROM {CATALOG}.{SCHEMA}.invoice i
        LEFT JOIN {CATALOG}.{SCHEMA}.invoice_line il ON il.invoice_id = i.invoice_id
        WHERE i.customer_id = '{cid}'
        GROUP BY i.invoice_id, i.billing_period, i.issue_date, i.due_date,
                 i.subtotal, i.discount_amount, i.tax_amount, i.total_due, i.status
        ORDER BY i.billing_period
    """

    latest_lines_q = f"""
        SELECT il.charge_type, il.description, il.amount
        FROM {CATALOG}.{SCHEMA}.invoice i
        JOIN {CATALOG}.{SCHEMA}.invoice_line il ON i.invoice_id = il.invoice_id
        WHERE i.customer_id = '{cid}'
          AND i.billing_period = (
            SELECT MAX(billing_period) FROM {CATALOG}.{SCHEMA}.invoice WHERE customer_id = '{cid}'
          )
        ORDER BY ABS(il.amount) DESC
    """

    trail, latest_lines = execute_queries_parallel([trail_q, latest_lines_q])
    return {"trail": trail, "latest_lines": latest_lines}


@router.get("/customer/{customer_id}/usage")
def customer_usage(customer_id: str) -> dict[str, Any]:
    """6-month usage trail aggregated at customer level (sums across subscriptions)."""
    if not customer_id.startswith("CUS-"):
        raise HTTPException(status_code=400, detail="customer_id must start with CUS-")
    cid = customer_id.replace("'", "''")
    rows = execute_query(f"""
        SELECT u.billing_period,
               SUM(u.voice_minutes_used) AS voice_min,
               SUM(u.data_mb_used)       AS data_mb,
               ROUND(SUM(u.data_mb_used) / 1024.0, 2) AS data_gb,
               SUM(u.sms_count)          AS sms,
               SUM(u.data_overage_mb)    AS overage_mb,
               ROUND(SUM(u.data_overage_mb) / 1024.0, 2) AS overage_gb,
               SUM(u.roaming_data_mb)    AS roaming_mb
        FROM {CATALOG}.{SCHEMA}.usage_summary u
        JOIN {CATALOG}.{SCHEMA}.subscription s ON u.subscription_id = s.subscription_id
        WHERE s.customer_id = '{cid}'
        GROUP BY u.billing_period
        ORDER BY u.billing_period
    """)
    return {"trail": rows}


@router.get("/customer/{customer_id}/contract")
def customer_contract(customer_id: str) -> dict[str, Any]:
    """Active contract details for Acciones tab."""
    if not customer_id.startswith("CUS-"):
        raise HTTPException(status_code=400, detail="customer_id must start with CUS-")
    cid = customer_id.replace("'", "''")
    rows = execute_query(f"""
        SELECT contract_id, signed_date, end_date, term_months,
               early_termination_fee, auto_renew, status,
               DATEDIFF(end_date, current_date()) AS days_remaining
        FROM {CATALOG}.{SCHEMA}.contract
        WHERE customer_id = '{cid}' AND status = 'active'
        ORDER BY end_date DESC LIMIT 1
    """)
    return {"contract": rows[0] if rows else None}


class SimulatePlanRequest(BaseModel):
    new_plan_id: str


@router.post("/customer/{customer_id}/action/simulate_plan_change")
def action_simulate_plan(customer_id: str, body: SimulatePlanRequest, lang: str = "es") -> dict[str, Any]:
    """Run simulate_plan_change UC function."""
    if not customer_id.startswith("CUS-"):
        raise HTTPException(status_code=400, detail="customer_id must start with CUS-")
    cid = customer_id.replace("'", "''")
    pid = body.new_plan_id.replace("'", "''")
    rows = execute_query(
        f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'simulate_plan_change')}('{cid}', '{pid}')"
    )
    return {"result": rows[0] if rows else None}


# ----------------------------------------------------------------------------
# Operational alerts — pre-written notices for the agent (start-of-shift huddle)
# ----------------------------------------------------------------------------

import random as _r



@router.get("/customer/alerts")
def customer_alerts(lang: str = "es") -> dict[str, Any]:
    """Return 1 alert per category. Disruption alert is randomized across a pool of
    regions to feel fresh each shift load. Hardcoded for demo."""
    from datetime import date
    today = date.today().isoformat()
    out: list[dict[str, Any]] = []
    rng = _r.Random()  # different sequence per call
    for i, (category, pool) in enumerate(i18n.alert_templates(lang).items(), start=1):
        t = rng.choice(pool)
        out.append({
            "id": f"AL-{i:03d}",
            "category": category,
            "severity": t.get("severity", "info"),
            "title": t["title"],
            "body": t["body"],
            "region": t.get("region"),
            "valid_from": today,
            "valid_to": t.get("valid_to"),
            "action_label": t.get("action_label"),
        })
    return {"alerts": out}


@router.get("/plans")
def list_plans() -> dict[str, Any]:
    """List active rate plans for the simulator dropdown."""
    rows = execute_query(f"""
        SELECT plan_id, plan_name, monthly_fee, data_quota_gb, voice_minutes
        FROM {CATALOG}.{SCHEMA}.rate_plan
        WHERE valid_to IS NULL
        ORDER BY monthly_fee ASC
    """)
    return {"plans": rows}


@router.post("/agent/chat")
def agent_chat(body: AgentChatRequest) -> dict[str, Any]:
    """Supervisor: Genie pulls structured data, ai_query polishes the executive answer."""
    try:
        w = _get_workspace_client()
        lang = body.lang or "es"

        # Optionally scope the question to a customer
        question = body.message
        if body.customer_id:
            question = i18n.scope_question(lang, body.customer_id, question)

        if body.conversation_id:
            msg = w.genie.create_message_and_wait(
                space_id=GENIE_SPACE_ID,
                conversation_id=body.conversation_id,
                content=question,
            )
        else:
            msg = w.genie.start_conversation_and_wait(
                space_id=GENIE_SPACE_ID,
                content=question,
            )

        extracted = _extract_genie_response(msg, w)
        genie_response_text = extracted["text"] or ""
        query_result = extracted["query_result"]
        genie_query = extracted["genie_query"]

        # Build a textual data summary for the supervisor prompt
        data_summary = ""
        if query_result:
            header, more_tmpl = i18n.data_summary_label(
                lang, len(query_result["rows"]), max(0, len(query_result["rows"]) - 10)
            )
            data_summary = header
            data_summary += " | ".join(query_result["columns"]) + "\n"
            for row in query_result["rows"][:10]:
                data_summary += " | ".join(row) + "\n"
            if len(query_result["rows"]) > 10:
                data_summary += more_tmpl.format(n=len(query_result["rows"]) - 10)

        supervisor_prompt = i18n.build_supervisor_prompt(
            lang, body.message, genie_response_text, data_summary
        )

        try:
            ai_sql = (
                "SELECT ai_query('databricks-claude-sonnet-4-5', '"
                + supervisor_prompt.replace("'", "''")
                + "') AS result"
            )
            ai_result = execute_query(ai_sql)
            supervisor_answer = (
                ai_result[0].get("result", "") if ai_result else ""
            ) or i18n.tr(lang, "supervisor.nosummary")
        except Exception as e:
            logger.exception("ai_query supervisor failed")
            supervisor_answer = (
                genie_response_text or i18n.tr(lang, "supervisor.error", e=type(e).__name__)
            )

        return {
            "conversation_id": msg.conversation_id,
            "supervisor_answer": supervisor_answer,
            "genie_query": genie_query,
            "genie_data": query_result,
            "genie_raw_reply": genie_response_text,
        }
    except Exception:
        logger.exception("Agent chat error")
        raise HTTPException(status_code=500, detail="Agent chat failed. Please try again.")


# ----------------------------------------------------------------------------
# Memory Agent chat (customer-360) — calls the Phase-1 memory agent app
# ----------------------------------------------------------------------------

def _build_customer_context(customer_id: str, lang: Any) -> Optional[str]:
    """Compact live-status summary (same UC functions as the profile chips: discount / payment-
    dunning / next-best-offer) to seed the agent's opening awareness. Returns None on any issue."""
    if not customer_id or not customer_id.startswith("CUS-"):
        return None
    cid = customer_id.replace("'", "''")
    try:
        discount, payment, nbo = execute_queries_parallel([
            f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'check_discount_status')}('{cid}')",
            f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'get_payment_status')}('{cid}')",
            f"SELECT * FROM {CATALOG}.{SCHEMA}.{_fn(lang, 'get_next_best_offer')}('{cid}')",
        ])
    except Exception:
        logger.warning("customer_context build failed", exc_info=True)
        return None

    parts: list[str] = []
    if discount and discount[0].get("reason"):
        parts.append(f"Descuento/Discount: {discount[0]['reason']}")
    if payment and payment[0].get("outstanding_balance") is not None:
        p = payment[0]
        parts.append(
            f"Pagos/Payments: saldo {p.get('outstanding_balance')}, {p.get('days_overdue')} días "
            f"mora, dunning {p.get('dunning_stage')}. {p.get('next_action') or ''}".strip()
        )
    if nbo and nbo[0].get("rationale"):
        n = nbo[0]
        parts.append(
            f"NBO: {n.get('recommended_plan')} (ahorro/savings {n.get('monthly_savings')}). "
            f"{n['rationale']}"
        )
    ctx = " | ".join(p for p in parts if p)
    return ctx or None


@router.post("/memory/chat")
async def memory_chat(body: MemoryChatRequest) -> dict[str, Any]:
    """Customer-360 chat backed by the memory agent (short + long-term memory on Lakebase).

    Passes customer_id (scope → subscriber memory) + thread_id (session → short-term) so the
    agent recalls the selected customer without a phone lookup. On the first turn of a session
    (no thread_id) it also attaches a live customer_context (discount / dunning / NBO) so the
    agent opens aware of the same status the customer-360 header shows.
    """
    import uuid
    from server.agent.billing_agent import answer as agent_answer

    thread_id = body.thread_id or str(uuid.uuid4())
    customer_context = None
    if body.customer_id and not body.thread_id:
        # first turn only — seed the agent with the same live status the header shows
        customer_context = _build_customer_context(body.customer_id, body.lang or "es")

    try:
        text = await agent_answer(message=body.message, thread_id=thread_id,
                                  customer_id=body.customer_id, customer_context=customer_context)
    except Exception:
        logger.exception("Embedded agent call failed")
        raise HTTPException(status_code=502, detail="Assistant is unavailable. Please try again.")

    return {"answer": text or i18n.tr(body.lang or "es", "genie.noAnswer"), "thread_id": thread_id}
