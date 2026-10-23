# Evidence — Genie Room (NL query over gold)

> Original build run (2026-08-31). Current numbers for the demo: [`run_2026-10-23.md`](run_2026-10-23.md) (data is synthetic and date-relative, so figures move each regeneration).

Genie Space created programmatically from a notebook (`12_genie`) over the AcmeTel gold model:
10 tables + 6 example question→SQL pairs + 9 join specs + thin instructions (UC comments
auto-read). Idempotent by title (create, else update).

- Space: `AcmeTel Billing Assistant` — id `01f1a591f61715668706a3321c36900e`
- Warehouse: `2f3030c18eff5d1a` (serverless)

## Live NL→SQL→answer (Conversation API) — COMPLETED

Question: *"How much revenue is at risk from customers 60+ days delinquent?"*

Genie-generated SQL (correctly used the metric view + MEASURE):
```sql
SELECT MEASURE(`revenue_at_risk`) AS `revenue_at_risk`,
       MEASURE(`customers_at_risk`) AS `customers`
FROM `dt_serverless_stable_isqgt5_catalog`.`acmetel_gold`.`mv_revenue_at_risk`
```

Answer:
```
Revenue at risk is 657.32 across 13 customers in mv_revenue_at_risk.
```
Matches the value computed independently via the UC function path ($657.32, dunning >= 3).

_Last updated: 2026-08-31_
