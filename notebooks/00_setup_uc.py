# Databricks notebook source
# MAGIC %run ./config

# COMMAND ----------
# medallion schemas + landing volume
for s in (LANDING, BRONZE, SILVER, GOLD):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{s}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{LANDING}.{VOLUME}")

# COMMAND ----------
# gold table contracts
GOLD_DDL = f"""
CREATE TABLE IF NOT EXISTS {t(GOLD,'customer')} (
  customer_id      STRING NOT NULL COMMENT 'Unique customer identifier, format CUS-NNNNNN',
  full_name        STRING          COMMENT 'Full name of the account holder',
  tax_id           STRING          COMMENT 'National ID or tax identification document',
  segment          STRING          COMMENT 'Commercial segment: consumer | smb | enterprise',
  status           STRING          COMMENT 'Account status: active | suspended | churned',
  signup_date      DATE            COMMENT 'Date the customer signed up',
  email            STRING          COMMENT 'Primary contact email',
  msisdn_primary   STRING          COMMENT 'Primary MSISDN (phone number) tied to the account'
) COMMENT 'Master of AcmeTel end customers. One row per customer. Joins to subscription, contract, invoice and payment via customer_id';

CREATE TABLE IF NOT EXISTS {t(GOLD,'rate_plan')} (
  plan_id              STRING  NOT NULL COMMENT 'Plan ID',
  plan_name            STRING            COMMENT 'Commercial plan name, e.g. "AcmeTel Pro 30GB"',
  monthly_fee          DECIMAL(10,2)     COMMENT 'Base monthly fee in USD',
  data_quota_gb        INT               COMMENT 'GB of data included in the plan',
  voice_minutes        INT               COMMENT 'Voice minutes included. -1 = unlimited',
  sms_quota            INT               COMMENT 'SMS included. -1 = unlimited',
  data_overage_per_gb  DECIMAL(10,2)     COMMENT 'USD charge per GB over the plan quota',
  valid_from           DATE              COMMENT 'Date the plan became available',
  valid_to             DATE              COMMENT 'Date the plan was retired. NULL if still active'
) COMMENT 'Catalog of AcmeTel postpaid service plans (active and retired). Each subscription points to a plan_id';

CREATE TABLE IF NOT EXISTS {t(GOLD,'subscription')} (
  subscription_id        STRING NOT NULL COMMENT 'Unique service/line ID',
  customer_id            STRING          COMMENT 'FK to customer.customer_id — owner of the service',
  plan_id                STRING          COMMENT 'FK to rate_plan.plan_id — current plan for this line',
  msisdn                 STRING          COMMENT 'Phone number (MSISDN) of the line',
  activation_date        DATE            COMMENT 'Date the line was activated',
  status                 STRING          COMMENT 'Status: active | suspended | terminated',
  device_imei            STRING          COMMENT 'IMEI of the associated device (may be NULL)',
  device_subsidy_amount  DECIMAL(10,2)   COMMENT 'Remaining device subsidy balance. >0 means the device is still being paid in installments'
) COMMENT 'Active AcmeTel lines/services. A customer can hold several subscriptions (family plan)';

CREATE TABLE IF NOT EXISTS {t(GOLD,'contract')} (
  contract_id              STRING NOT NULL COMMENT 'Contract ID',
  customer_id              STRING          COMMENT 'FK to customer.customer_id',
  subscription_id          STRING          COMMENT 'FK to subscription.subscription_id (1:1 with contract)',
  signed_date              DATE            COMMENT 'Date the contract was signed',
  term_months              INT             COMMENT 'Minimum commitment in months: 12, 18 or 24',
  end_date                 DATE            COMMENT 'Contract end date (signed_date + term_months)',
  early_termination_fee    DECIMAL(10,2)   COMMENT 'USD penalty for cancelling before the contract ends',
  auto_renew               BOOLEAN         COMMENT 'TRUE if the contract auto-renews at expiry',
  status                   STRING          COMMENT 'Status: active | expired | cancelled'
) COMMENT 'Formal contracts tied to each subscription. Defines commitment, cancellation penalty and renewal';

CREATE TABLE IF NOT EXISTS {t(GOLD,'promotion')} (
  promo_id           STRING NOT NULL COMMENT 'Promotion ID',
  promo_name         STRING          COMMENT 'Commercial name, e.g. "Loyalty Discount 20%"',
  discount_type      STRING          COMMENT 'Discount type: percent | fixed_amount | free_data',
  discount_value     DECIMAL(10,2)   COMMENT 'Discount value. percent=%, fixed_amount=USD, free_data=GB',
  duration_months    INT             COMMENT 'Total benefit duration in months',
  eligibility_rule   STRING          COMMENT 'Eligibility rule described in free text'
) COMMENT 'Catalog of discounts and promotions available at AcmeTel';

CREATE TABLE IF NOT EXISTS {t(GOLD,'subscription_promotion')} (
  sub_promo_id     STRING NOT NULL COMMENT 'ID of a promotion applied to a service',
  subscription_id  STRING          COMMENT 'FK to subscription.subscription_id',
  promo_id         STRING          COMMENT 'FK to promotion.promo_id',
  start_date       DATE            COMMENT 'Date the promotion started applying to the service',
  end_date         DATE            COMMENT 'Date the promotion stopped applying (discount expiry)',
  status           STRING          COMMENT 'Status: active | expired | cancelled. expired means the discount no longer applies'
) COMMENT 'Bridge table linking promotions applied to each subscription with their validity dates. To answer "why did my bill go up?" or "do I still have the discount?", look here';

CREATE TABLE IF NOT EXISTS {t(GOLD,'invoice')} (
  invoice_id        STRING NOT NULL COMMENT 'Unique invoice ID',
  customer_id       STRING          COMMENT 'FK to customer.customer_id — billed customer',
  billing_period    STRING          COMMENT 'Billed period in YYYY-MM format',
  issue_date        DATE            COMMENT 'Issue date',
  due_date          DATE            COMMENT 'Payment due date (issue_date + 15 days by default)',
  subtotal          DECIMAL(10,2)   COMMENT 'Sum of charges before discounts and taxes',
  discount_amount   DECIMAL(10,2)   COMMENT 'Total discounts applied (positive value)',
  tax_amount        DECIMAL(10,2)   COMMENT 'Taxes applied',
  total_due         DECIMAL(10,2)   COMMENT 'Final amount due = subtotal - discount_amount + tax_amount',
  status            STRING          COMMENT 'Status: paid | partial | overdue | unpaid'
) COMMENT 'Invoices issued monthly to each customer. One row per customer per month. For charge detail see invoice_line';

CREATE TABLE IF NOT EXISTS {t(GOLD,'invoice_line')} (
  invoice_line_id   STRING NOT NULL COMMENT 'Unique line ID',
  invoice_id        STRING          COMMENT 'FK to invoice.invoice_id',
  subscription_id   STRING          COMMENT 'FK to subscription.subscription_id (the line is tied to a service)',
  charge_type       STRING          COMMENT 'Charge type: recurring | usage_overage | device_subsidy | discount | one_time | tax',
  description       STRING          COMMENT 'Customer-readable description, e.g. "Pro 30GB Plan - April 2026"',
  amount            DECIMAL(10,2)   COMMENT 'Amount in USD. Positive for charges, negative for discounts'
) COMMENT 'Line-by-line detail of each invoice. Explains exactly what was charged and why it went up or down vs the prior month';

CREATE TABLE IF NOT EXISTS {t(GOLD,'payment')} (
  payment_id      STRING NOT NULL COMMENT 'Payment attempt ID',
  invoice_id      STRING          COMMENT 'FK to invoice.invoice_id',
  customer_id     STRING          COMMENT 'FK to customer.customer_id',
  payment_date    DATE            COMMENT 'Date the payment was made. NULL if not yet paid',
  amount          DECIMAL(10,2)   COMMENT 'Amount paid',
  method          STRING          COMMENT 'Payment method: card | bank_transfer | cash | app',
  status          STRING          COMMENT 'Payment result: success | failed | pending',
  dunning_stage   INT             COMMENT 'Collections stage: 0=current, 1=1-30d, 2=31-60d, 3=61-90d, 4=>90d (service cut)'
) COMMENT 'Payments and collections status per invoice. dunning_stage indicates delinquency risk. For "how much do I owe?" or "what if I do not pay?" look here';

CREATE TABLE IF NOT EXISTS {t(GOLD,'usage_summary')} (
  subscription_id     STRING NOT NULL COMMENT 'FK to subscription.subscription_id',
  billing_period      STRING NOT NULL COMMENT 'Usage period in YYYY-MM format',
  voice_minutes_used  INT             COMMENT 'Voice minutes consumed in the period',
  data_mb_used        BIGINT          COMMENT 'MB of data consumed in the period',
  sms_count           INT             COMMENT 'Number of SMS sent',
  data_overage_mb     BIGINT          COMMENT 'MB of data over the plan quota. >0 means billable overage',
  roaming_data_mb     BIGINT          COMMENT 'MB consumed on international roaming (billed separately)'
) COMMENT 'Monthly usage summary per line/subscription. Cross against rate_plan.data_quota_gb to explain high usage';
"""

for stmt in [s.strip() for s in GOLD_DDL.split(";") if s.strip()]:
    spark.sql(stmt)

# COMMAND ----------
print("catalog:", CATALOG)
print("schemas:", [r.databaseName for r in spark.sql(f"SHOW SCHEMAS IN {CATALOG}").collect()])
print("gold tables:", [r.tableName for r in spark.sql(f"SHOW TABLES IN {CATALOG}.{GOLD}").collect()])
