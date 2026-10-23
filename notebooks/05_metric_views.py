# Databricks notebook source
# MAGIC %run ./config

# COMMAND ----------
G = f"{CATALOG}.{GOLD}"

# COMMAND ----------
# 1. ARPU monthly
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_arpu_monthly
WITH METRICS LANGUAGE YAML
COMMENT 'KPI: monthly ARPU (total revenue / unique billed customers) by period'
AS $$
version: 1.1
source: SELECT * FROM {G}.invoice
dimensions:
  - name: billing_period
    expr: billing_period
    display_name: Billing period
  - name: status
    expr: status
    display_name: Invoice status
measures:
  - name: total_revenue
    expr: SUM(total_due)
    display_name: Total revenue
    format: {{type: currency, currency_code: USD}}
  - name: invoice_count
    expr: COUNT(*)
    display_name: Invoice count
  - name: customers_billed
    expr: COUNT(DISTINCT customer_id)
    display_name: Customers billed
  - name: arpu
    expr: SUM(total_due) / COUNT(DISTINCT customer_id)
    display_name: ARPU
    format: {{type: currency, currency_code: USD}}
$$
""")

# COMMAND ----------
# 2. collection rate
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_collection_rate
WITH METRICS LANGUAGE YAML
COMMENT 'KPI: share of invoices paid vs issued, by period and segment'
AS $$
version: 1.1
source: |
  SELECT i.*, c.segment
  FROM {G}.invoice i
  LEFT JOIN {G}.customer c ON i.customer_id = c.customer_id
dimensions:
  - name: billing_period
    expr: billing_period
    display_name: Period
  - name: segment
    expr: segment
    display_name: Segment
measures:
  - name: total_invoices
    expr: COUNT(*)
    display_name: Total invoices
  - name: paid_invoices
    expr: SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)
    display_name: Paid invoices
  - name: collection_rate
    expr: SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
    display_name: Collection rate
    format: {{type: percentage}}
$$
""")

# COMMAND ----------
# 3. dunning distribution
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_dunning_distribution
WITH METRICS LANGUAGE YAML
COMMENT 'KPI: payment distribution by collections (dunning) stage. 0=current, 1=1-30d, 2=31-60d, 3=61-90d, 4=>90d (cut)'
AS $$
version: 1.1
source: SELECT * FROM {G}.payment
dimensions:
  - name: dunning_stage
    expr: dunning_stage
    display_name: Dunning stage
  - name: payment_status
    expr: status
    display_name: Payment status
  - name: method
    expr: method
    display_name: Payment method
measures:
  - name: payments_count
    expr: COUNT(*)
    display_name: Payments
  - name: customers_count
    expr: COUNT(DISTINCT customer_id)
    display_name: Unique customers
  - name: total_amount
    expr: SUM(amount)
    display_name: Amount paid
    format: {{type: currency, currency_code: USD}}
$$
""")

# COMMAND ----------
# 4. discounts expiring in 30d
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_discount_expiring_30d
WITH METRICS LANGUAGE YAML
COMMENT 'KRI: customers whose discount expires in the next 30 days. Input for retention and proactive outreach'
AS $$
version: 1.1
source: |
  SELECT sp.*, s.customer_id, s.plan_id, c.segment, p.promo_name
  FROM {G}.subscription_promotion sp
  JOIN {G}.subscription s ON sp.subscription_id = s.subscription_id
  JOIN {G}.customer c ON s.customer_id = c.customer_id
  JOIN {G}.promotion p ON sp.promo_id = p.promo_id
  WHERE sp.status = 'active'
    AND sp.end_date BETWEEN current_date() AND date_add(current_date(), 30)
dimensions:
  - name: segment
    expr: segment
    display_name: Segment
  - name: promo_name
    expr: promo_name
    display_name: Promotion
  - name: end_date
    expr: end_date
    display_name: Expiry date
measures:
  - name: at_risk_count
    expr: COUNT(DISTINCT customer_id)
    display_name: Customers at risk
  - name: subscriptions_count
    expr: COUNT(DISTINCT subscription_id)
    display_name: Services affected
$$
""")

# COMMAND ----------
# 5. overage frequency by plan
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_overage_frequency
WITH METRICS LANGUAGE YAML
COMMENT 'KPI: share of subscriptions with data overage in the period, by plan. Flags mis-sized plans'
AS $$
version: 1.1
source: |
  SELECT u.*, s.customer_id, rp.plan_name
  FROM {G}.usage_summary u
  JOIN {G}.subscription s ON u.subscription_id = s.subscription_id
  JOIN {G}.rate_plan rp ON s.plan_id = rp.plan_id
dimensions:
  - name: plan_name
    expr: plan_name
    display_name: Plan
  - name: billing_period
    expr: billing_period
    display_name: Period
measures:
  - name: total_subs
    expr: COUNT(*)
    display_name: Services measured
  - name: subs_with_overage
    expr: SUM(CASE WHEN data_overage_mb > 0 THEN 1 ELSE 0 END)
    display_name: Services with overage
  - name: overage_rate
    expr: SUM(CASE WHEN data_overage_mb > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
    display_name: "% with overage"
    format: {{type: percentage}}
  - name: total_overage_mb
    expr: SUM(data_overage_mb)
    display_name: Total overage MB
$$
""")

# COMMAND ----------
# 6. contracts expiring in 60d
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_contract_expiring_60d
WITH METRICS LANGUAGE YAML
COMMENT 'KRI: contracts whose commitment ends in the next 60 days. Critical window for retention and renegotiation'
AS $$
version: 1.1
source: |
  SELECT ct.*, c.segment, c.full_name
  FROM {G}.contract ct
  JOIN {G}.customer c ON ct.customer_id = c.customer_id
  WHERE ct.status = 'active'
    AND ct.end_date BETWEEN current_date() AND date_add(current_date(), 60)
dimensions:
  - name: segment
    expr: segment
    display_name: Segment
  - name: end_date
    expr: end_date
    display_name: Contract end date
  - name: term_months
    expr: term_months
    display_name: Term (months)
measures:
  - name: contracts_count
    expr: COUNT(*)
    display_name: Contracts expiring
  - name: customers_count
    expr: COUNT(DISTINCT customer_id)
    display_name: Unique customers
  - name: total_etf
    expr: SUM(early_termination_fee)
    display_name: Total ETF exposed
    format: {{type: currency, currency_code: USD}}
$$
""")

# COMMAND ----------
# 7. plan utilization
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_plan_utilization
WITH METRICS LANGUAGE YAML
COMMENT 'KPI: average data-quota utilization by plan. <30% under-uses (downgrade candidate); >100% has overage'
AS $$
version: 1.1
source: |
  SELECT u.*, s.customer_id, rp.plan_name, rp.data_quota_gb,
         u.data_mb_used / (rp.data_quota_gb * 1024.0) AS utilization_ratio
  FROM {G}.usage_summary u
  JOIN {G}.subscription s ON u.subscription_id = s.subscription_id
  JOIN {G}.rate_plan rp ON s.plan_id = rp.plan_id
dimensions:
  - name: plan_name
    expr: plan_name
    display_name: Plan
  - name: billing_period
    expr: billing_period
    display_name: Period
measures:
  - name: avg_utilization
    expr: AVG(utilization_ratio)
    display_name: Average utilization
    format: {{type: percentage}}
  - name: total_data_mb
    expr: SUM(data_mb_used)
    display_name: Data consumed (MB)
  - name: subs_count
    expr: COUNT(DISTINCT subscription_id)
    display_name: Services
$$
""")

# COMMAND ----------
# 8. revenue at risk (dunning 60+)
spark.sql(f"""
CREATE OR REPLACE VIEW {G}.mv_revenue_at_risk
WITH METRICS LANGUAGE YAML
COMMENT 'KRI: total billed USD unpaid for customers with dunning_stage >= 3 (61+ days delinquent). Top executive collections indicator'
AS $$
version: 1.1
source: |
  SELECT p.*, i.total_due, i.billing_period, c.segment, c.full_name
  FROM {G}.payment p
  JOIN {G}.invoice i ON p.invoice_id = i.invoice_id
  JOIN {G}.customer c ON p.customer_id = c.customer_id
  WHERE p.dunning_stage >= 3
dimensions:
  - name: dunning_stage
    expr: dunning_stage
    display_name: Dunning stage
  - name: segment
    expr: segment
    display_name: Segment
  - name: billing_period
    expr: billing_period
    display_name: Period
measures:
  - name: revenue_at_risk
    expr: SUM(total_due)
    display_name: Revenue at risk
    format: {{type: currency, currency_code: USD}}
  - name: customers_at_risk
    expr: COUNT(DISTINCT customer_id)
    display_name: Delinquent customers
$$
""")

# COMMAND ----------
mvs = [r.table_name for r in spark.sql(f"""
    SELECT table_name FROM {CATALOG}.information_schema.tables
    WHERE table_schema='{GOLD}' AND table_type='METRIC_VIEW' ORDER BY 1""").collect()]
print(f"metric views: {len(mvs)}")
for m in mvs:
    print(" ", m)

# COMMAND ----------
# CREATE OR REPLACE drops grants: re-grant the app service principal if the app exists
from databricks.sdk import WorkspaceClient
try:
    sp_id = WorkspaceClient().apps.get(APP_NAME).service_principal_client_id
except Exception:
    sp_id = None
for m in mvs if sp_id else []:
    spark.sql(f"GRANT SELECT ON VIEW {G}.{m} TO `{sp_id}`")
print(f"app grants: {len(mvs) if sp_id else 0} views -> {sp_id or 'no app yet'}")
