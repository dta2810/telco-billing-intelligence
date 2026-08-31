# Evidence — Part 1: setup + raw generation

Workspace: FEVM `fevm-dt-serverless-stable-isqgt5` · serverless · catalog `dt_serverless_stable_isqgt5_catalog`.
Run via one-time serverless Job runs on the imported notebooks.

## 00_setup_uc — SUCCESS

Schemas created:
```
acmetel_bronze
acmetel_gold
acmetel_landing
acmetel_silver
```

Gold tables created (10):
```
contract  customer  invoice  invoice_line  payment
promotion  rate_plan  subscription  subscription_promotion  usage_summary
```

Column comments in place (sample, gold.customer):
```
customer_id  Unique customer identifier, format CUS-NNNNNN
full_name    Full name of the account holder
tax_id       National ID or tax identification document
```

## 01_generate_raw — SUCCESS

Raw CSV landed in `/Volumes/dt_serverless_stable_isqgt5_catalog/acmetel_landing/raw/<entity>/`.

Row counts (read via `read_files` over the landed CSVs):
```
customer                   300
rate_plan                   10
subscription               376
contract                   376
promotion                   15
subscription_promotion     500
invoice                   1800
invoice_line              5981
payment                   1500
usage_summary             1600
```

Seeded business scenarios (the story):
```
expired discounts (subscription_promotion.status='expired')   234
delinquent payments (dunning_stage >= 1)                        40
overdue invoices (status='overdue')                             40
usage rows with billable overage (data_overage_mb > 0)         174
```

## 02_bronze — SUCCESS

Auto Loader (`cloudFiles`, CSV, `availableNow`) raw → bronze. All columns string plus
`_rescued_data`, `_ingested_at`, `_source_file`. Bronze row counts (parity with raw):
```
customer                   300
rate_plan                   10
subscription               376
contract                   376
promotion                   15
subscription_promotion     500
invoice                   1800
invoice_line              5981
payment                   1500
usage_summary             1600
```

## 03_silver — SUCCESS

Cast bronze (string) → gold contract types (read from `information_schema`), dedup on PK,
drop null keys. Row counts equal bronze (clean synthetic data, 0 removed). Type checks:
```
customer.signup_date   date
invoice.total_due      decimal(10,2)
payment.dunning_stage  int
contract.auto_renew    boolean
```
Null `payment_date` preserved for the 40 delinquent (overdue) customers.

## 04_gold — SUCCESS

`INSERT OVERWRITE` gold ← silver (preserves the table contract + comments — not `saveAsTable`).
Gold row counts equal silver (300/10/376/376/15/500/1800/5981/1500/1600). Column comments
intact after load: **77 gold columns with comment**. Business check — revenue at risk
(dunning_stage ≥ 3) = **$657.32**.

## 05_metric_views — SUCCESS

8 metric views created on gold (parametrized to the real catalog/schema). Listed via
`information_schema.tables` where `table_type='METRIC_VIEW'`:
```
mv_arpu_monthly          mv_dunning_distribution   mv_plan_utilization
mv_collection_rate       mv_discount_expiring_30d  mv_revenue_at_risk
mv_contract_expiring_60d mv_overage_frequency
```
Queried live — ARPU by billing period (`MEASURE(arpu)`, `MEASURE(total_revenue)`):
```
2026-03   58.69   17605.61
2026-04   58.67   17599.77
2026-05   59.86   17956.58
2026-06   58.07   17422.27
2026-07   59.36   17807.46
2026-08   61.93   18578.92
```

## Validation notebook (06_validate)

Covers, per run, as an HTML report + text: UC structure (schemas, gold tables, comments),
landing raw counts, seeded scenarios, **medallion layer parity (bronze = silver = gold)**, and
**metric views (8)**. David runs it and downloads the HTML.

_Last updated: 2026-08-31_
