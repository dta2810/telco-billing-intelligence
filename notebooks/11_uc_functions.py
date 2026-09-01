# Databricks notebook source
# MAGIC %run ./config

# COMMAND ----------
G = f"{CATALOG}.{GOLD}"

# COMMAND ----------
# 1. check_discount_status — active discount? when does it expire?
spark.sql(f"""
CREATE OR REPLACE FUNCTION {G}.check_discount_status(
  p_customer_id STRING COMMENT 'Customer ID, format CUS-NNNNNN'
)
RETURNS TABLE (
  status            STRING COMMENT 'active | expiring_soon | expired (<=60d, affects current/prior cycle) | no_active_discount (expired >60d) | no_discount',
  promo_name        STRING COMMENT 'Most relevant promotion name',
  end_date          DATE   COMMENT 'Discount expiry date',
  days_to_expire    INT    COMMENT 'Days remaining (negative if already expired)',
  last_discount_amt DECIMAL(10,2) COMMENT 'Numeric value of the last discount (% or USD)',
  reason            STRING COMMENT 'Customer-readable explanation'
)
COMMENT 'Returns the status of the customer''s most recent discount. expired only if it lapsed within the last 60 days (likely cause of this month''s increase); older than that, status = no_active_discount (historical context, not the current cause).'
RETURN
  WITH latest AS (
    SELECT sp.*, p.promo_name, p.discount_value,
           ROW_NUMBER() OVER (PARTITION BY s.customer_id ORDER BY sp.end_date DESC) AS rn
    FROM {G}.subscription_promotion sp
    JOIN {G}.subscription s ON sp.subscription_id = s.subscription_id
    JOIN {G}.promotion p    ON sp.promo_id = p.promo_id
    WHERE s.customer_id = p_customer_id
  )
  SELECT
    CASE
      WHEN end_date < current_date() AND DATEDIFF(current_date(), end_date) <= 60 THEN 'expired'
      WHEN end_date < current_date()                                              THEN 'no_active_discount'
      WHEN end_date <= date_add(current_date(), 30)                               THEN 'expiring_soon'
      WHEN status = 'active'                                                      THEN 'active'
      ELSE 'no_discount'
    END AS status,
    promo_name, end_date,
    DATEDIFF(end_date, current_date()) AS days_to_expire,
    discount_value AS last_discount_amt,
    CASE
      WHEN end_date < current_date() AND DATEDIFF(current_date(), end_date) <= 60 THEN
        concat('Your discount "', promo_name, '" expired on ', cast(end_date AS STRING),
               '. That is why your bill went up this month.')
      WHEN end_date < current_date() THEN
        concat('Your discount "', promo_name, '" ended ',
               cast(DATEDIFF(current_date(), end_date) AS STRING), ' days ago (',
               cast(end_date AS STRING), '). This month''s increase comes from another cause.')
      WHEN end_date <= date_add(current_date(), 30) THEN
        concat('Your discount "', promo_name, '" expires in ',
               cast(DATEDIFF(end_date, current_date()) AS STRING), ' days (', cast(end_date AS STRING), ').')
      WHEN status = 'active' THEN
        concat('Your discount "', promo_name, '" is still active until ', cast(end_date AS STRING), '.')
      ELSE 'You do not have an active discount right now.'
    END AS reason
  FROM latest WHERE rn = 1
""")

# COMMAND ----------
# 2. get_payment_status — balance, days overdue, next action
spark.sql(f"""
CREATE OR REPLACE FUNCTION {G}.get_payment_status(
  p_customer_id STRING COMMENT 'Customer ID'
)
RETURNS TABLE (
  outstanding_balance DECIMAL(10,2) COMMENT 'Total outstanding balance',
  oldest_due_date     DATE          COMMENT 'Oldest unpaid due date',
  days_overdue        INT           COMMENT 'Days since the oldest due date (0 if current)',
  dunning_stage       INT           COMMENT '0=current, 1=1-30d, 2=31-60d, 3=61-90d, 4=>90d',
  next_action         STRING        COMMENT 'Recommended next collections action'
)
COMMENT 'Summary of the customer''s collections status. Useful for "how much do I owe?" or "what if I do not pay?"'
RETURN
  WITH unpaid AS (
    SELECT i.customer_id,
           SUM(i.total_due) AS outstanding_balance,
           MIN(i.due_date)  AS oldest_due_date,
           MAX(p.dunning_stage) AS dunning_stage
    FROM {G}.invoice i
    LEFT JOIN {G}.payment p ON i.invoice_id = p.invoice_id
    WHERE i.customer_id = p_customer_id AND i.status IN ('overdue','unpaid','partial')
    GROUP BY i.customer_id
  )
  SELECT
    coalesce(outstanding_balance, 0) AS outstanding_balance,
    oldest_due_date,
    coalesce(DATEDIFF(current_date(), oldest_due_date), 0) AS days_overdue,
    coalesce(dunning_stage, 0) AS dunning_stage,
    CASE
      WHEN outstanding_balance IS NULL OR outstanding_balance = 0 THEN 'Customer is current. No action required.'
      WHEN dunning_stage = 1 THEN 'Send a friendly payment reminder.'
      WHEN dunning_stage = 2 THEN 'Collections call. Offer a payment plan.'
      WHEN dunning_stage = 3 THEN 'Formal delinquency notice. Suspension risk.'
      WHEN dunning_stage >= 4 THEN 'Service suspension / cut-off.'
      ELSE 'Review the case manually.'
    END AS next_action
  FROM unpaid
""")

# COMMAND ----------
# 3. get_next_best_offer — plan recommendation from real usage
spark.sql(f"""
CREATE OR REPLACE FUNCTION {G}.get_next_best_offer(
  p_customer_id STRING COMMENT 'Customer ID'
)
RETURNS TABLE (
  current_plan     STRING        COMMENT 'Current plan',
  current_fee      DECIMAL(10,2) COMMENT 'Current monthly fee',
  recommended_plan STRING        COMMENT 'Recommended plan (same if none better)',
  recommended_fee  DECIMAL(10,2) COMMENT 'Recommended plan monthly fee',
  monthly_savings  DECIMAL(10,2) COMMENT 'Estimated monthly saving (positive = saves; negative = pays more but better fit)',
  rationale        STRING        COMMENT 'Reason for the recommendation'
)
COMMENT 'Recommends the plan that best fits the customer''s last-3-months usage. Ranking: the cheapest plan whose quota covers the monthly PEAK with 10% margin (not the average, to not hide spikes that cause overage). Rationale considers overage_months and low usage.'
RETURN
  WITH usage_3m AS (
    SELECT s.customer_id,
           AVG(u.data_mb_used) AS avg_data_mb,
           MAX(u.data_mb_used) AS peak_data_mb,
           SUM(CASE WHEN u.data_overage_mb > 0 THEN 1 ELSE 0 END) AS overage_months
    FROM {G}.usage_summary u
    JOIN {G}.subscription s ON u.subscription_id = s.subscription_id
    WHERE s.customer_id = p_customer_id
      AND u.billing_period >= date_format(add_months(current_date(), -3), 'yyyy-MM')
    GROUP BY s.customer_id
  ),
  cur AS (
    SELECT s.customer_id, rp.plan_name, rp.monthly_fee, rp.data_quota_gb
    FROM {G}.subscription s
    JOIN {G}.rate_plan rp ON s.plan_id = rp.plan_id
    WHERE s.customer_id = p_customer_id
    ORDER BY s.activation_date DESC LIMIT 1
  ),
  candidates AS (
    SELECT plan_name, monthly_fee, data_quota_gb FROM {G}.rate_plan WHERE valid_to IS NULL
  ),
  best AS (
    SELECT c.plan_name AS current_plan, c.monthly_fee AS current_fee, c.data_quota_gb AS current_quota,
           u.avg_data_mb, u.peak_data_mb, u.overage_months,
           cand.plan_name AS recommended_plan, cand.monthly_fee AS recommended_fee,
           c.monthly_fee - cand.monthly_fee AS monthly_savings,
           ROW_NUMBER() OVER (
             ORDER BY CASE WHEN cand.data_quota_gb * 1024 >= COALESCE(u.peak_data_mb, 0) * 1.1 THEN 0 ELSE 1 END,
                      cand.monthly_fee ASC
           ) AS rn
    FROM cur c CROSS JOIN candidates cand LEFT JOIN usage_3m u ON c.customer_id = u.customer_id
  )
  SELECT current_plan, current_fee, recommended_plan, recommended_fee, monthly_savings,
    CASE
      WHEN overage_months >= 1 AND recommended_plan <> current_plan THEN
        concat('You exceeded your quota in ', cast(overage_months AS STRING),
               ' of the last 3 months (peak ', cast(ROUND(peak_data_mb / 1024.0, 1) AS STRING),
               ' GB). ', recommended_plan, ' covers your peak with margin and cuts overage cost.')
      WHEN overage_months >= 1 AND recommended_plan = current_plan THEN
        concat('You had overage in ', cast(overage_months AS STRING),
               ' of the last 3 months, but your plan is still the best fit. Consider adjusting usage or accepting the overage.')
      WHEN avg_data_mb < current_quota * 1024 * 0.3 THEN
        'You have used less than 30% of your plan in the last 3 months. You can switch to a cheaper plan on request.'
      WHEN current_plan = recommended_plan THEN
        'Your current plan covers your usage (including your peak) with margin. Keep it.'
      ELSE 'We suggest a plan that better fits your recent usage.'
    END AS rationale
  FROM best WHERE rn = 1
""")

# COMMAND ----------
# 4. simulate_plan_change — current cost vs new plan cost
spark.sql(f"""
CREATE OR REPLACE FUNCTION {G}.simulate_plan_change(
  p_customer_id STRING COMMENT 'Customer ID',
  p_new_plan_id STRING COMMENT 'Plan ID to switch to (PLAN-NNN)'
)
RETURNS TABLE (
  current_plan     STRING,
  current_fee      DECIMAL(10,2),
  current_data_gb  INT,
  current_voice_min INT,
  current_sms      INT,
  new_plan         STRING,
  new_fee          DECIMAL(10,2),
  new_data_gb      INT,
  new_voice_min    INT,
  new_sms          INT,
  monthly_delta    DECIMAL(10,2) COMMENT 'Monthly difference (positive = costlier, negative = saves)',
  annual_delta     DECIMAL(10,2),
  data_delta_gb    INT           COMMENT 'GB difference (new - current)',
  voice_delta_min  INT           COMMENT 'Voice minutes difference (new - current; -1 plans excluded)',
  warning          STRING        COMMENT 'Warnings: ETF, downgrade causing overage, etc.'
)
COMMENT 'Simulates the economic impact of a plan change. Compares current vs new monthly fee, data/voice/SMS allowances and deltas, computes annual impact, and warns about the Early Termination Fee if a contract is active and about overage risk if the new plan has less quota.'
RETURN
  WITH cur AS (
    SELECT s.customer_id, rp.plan_name AS current_plan, rp.monthly_fee AS current_fee,
           rp.data_quota_gb AS current_quota, rp.voice_minutes AS current_voice, rp.sms_quota AS current_sms
    FROM {G}.subscription s
    JOIN {G}.rate_plan rp ON s.plan_id = rp.plan_id
    WHERE s.customer_id = p_customer_id
    ORDER BY s.activation_date DESC LIMIT 1
  ),
  new_p AS (
    SELECT plan_name AS new_plan, monthly_fee AS new_fee, data_quota_gb AS new_quota,
           voice_minutes AS new_voice, sms_quota AS new_sms
    FROM {G}.rate_plan WHERE plan_id = p_new_plan_id
  ),
  ct AS (
    SELECT MAX(early_termination_fee) AS etf, MAX(end_date) AS contract_end
    FROM {G}.contract WHERE customer_id = p_customer_id AND status = 'active'
  )
  SELECT current_plan, current_fee, cur.current_quota AS current_data_gb,
         cur.current_voice AS current_voice_min, cur.current_sms AS current_sms,
         new_plan, new_fee, new_p.new_quota AS new_data_gb,
         new_p.new_voice AS new_voice_min, new_p.new_sms AS new_sms,
         (new_fee - current_fee)      AS monthly_delta,
         (new_fee - current_fee) * 12 AS annual_delta,
         (new_p.new_quota - cur.current_quota) AS data_delta_gb,
         CASE WHEN new_p.new_voice = -1 OR cur.current_voice = -1 THEN 0
              ELSE new_p.new_voice - cur.current_voice END AS voice_delta_min,
         concat_ws(' ',
           CASE WHEN ct.contract_end > current_date() THEN
                concat('Active contract until ', cast(ct.contract_end AS STRING),
                       '; switching may apply a penalty of $', cast(ct.etf AS STRING), '.') ELSE '' END,
           CASE WHEN new_p.new_quota < cur.current_quota THEN
                concat('Careful: the new plan has ', cast(new_p.new_quota AS STRING),
                       'GB vs your current ', cast(cur.current_quota AS STRING),
                       'GB. Overage risk.') ELSE '' END
         ) AS warning
  FROM cur, new_p, ct
""")

# COMMAND ----------
fns = [r.routine_name for r in spark.sql(f"""
    SELECT routine_name FROM {CATALOG}.information_schema.routines
    WHERE routine_schema='{GOLD}' ORDER BY routine_name""").collect()]
print(f"UC functions in {G}: {len(fns)}")
for f in fns:
    print(" ", f)
