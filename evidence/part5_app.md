# Evidence — Databricks App (Customer-360 + embedded agent)

> Original build run (2026-08-31). Current numbers for the demo: [`run_2026-10-23.md`](run_2026-10-23.md) (data is synthetic and date-relative, so figures move each regeneration).

One Databricks App: FastAPI + React (Executive KPIs + Customer-360) with the memory agent
EMBEDDED in-process (no HTTP hop). Frontend built with vite, source synced to workspace,
deployed via notebook (`14_app`, SDK `w.apps`).

- App: `acmetel-billing-360` — RUNNING
- URL: https://acmetel-billing-360-7474655246214229.aws.databricksapps.com
- SP client_id: `99eb8489-3111-498f-a465-22df6d5c9caf`

## /api/health — OK
```
{"ok":true,"catalog":"dt_serverless_stable_isqgt5_catalog","schema":"acmetel_gold",
 "genie_space_id":"01f1a591f61715668706a3321c36900e","is_databricks_app":true}
```

## /api/smoke — OK (UC access through the app SP)
```
table_counts: {customer:300, subscription:376, invoice:1800, payment:1500}
check_discount_status('CUS-000002'): status=expired, promo="Pro Upgrade 2x1",
  reason="Your discount ... expired ... That is why your bill went up this month."
mv_arpu_monthly (last period): arpu=61.93, revenue=18578.92
```

## Deploy wiring done
- `14_app`: created app, granted SP → UC (USE CATALOG/SCHEMA, SELECT, EXECUTE on acmetel_gold) + Genie CAN_RUN.
- Added Lakebase `postgres` app resource (branch production / db databricks-postgres, CAN_CONNECT_AND_CREATE).
- Granted the app SP PG privileges on schema `acmetel_memory` (USAGE/CREATE + ALL on tables/sequences + default privileges).

## /api/memory/chat — WORKING end-to-end

Fix applied: wrap MCP tools so their result is a plain string (Claude rejects structured
tool_result content carrying an `id`). After redeploy:

Single-turn (UC functions + discount status combined):
```
Q: How much does this customer owe and why?  (customer_id=CUS-000002)
A: This customer owes $92.61, 12 days overdue (due Aug 20, 2026). Account at dunning stage 3
   — formal delinquency notice with suspension risk. The higher bill this month is because the
   "Pro Upgrade 2x1" discount expired on July 15, 2026.
```

Long-term memory, cross-session (the differentiator):
```
Turn 1 (thread A): "note this customer prefers WhatsApp and is price-sensitive"
  → agent calls save_user_memory (persisted to Lakebase acmetel_memory.store)
Turn 2 (NEW thread B, same customer): "What do we know about this customer?"
  → "they prefer WhatsApp and are price-sensitive" + live balance/discount/NBO
```
Proves: short-term (in-thread) + long-term (subscriber, across threads) memory on Lakebase,
Genie + UC functions as tools, all in one embedded agent inside the app.

## All six BAR stages working in one deployed app
Lakeflow (medallion) → Unity Catalog (gold + metric views) → Lakebase (agent memory) →
ML/GenAI (embedded agent) → Genie (NL query) → Databricks App (this surface).

_Last updated: 2026-08-31_
