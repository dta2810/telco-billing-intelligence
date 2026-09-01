# Databricks notebook source
# naming conventions

CATALOG = "dt_serverless_stable_isqgt5_catalog"
LANDING, BRONZE, SILVER, GOLD = "acmetel_landing", "acmetel_bronze", "acmetel_silver", "acmetel_gold"
VOLUME = "raw"
VOL_PATH = f"/Volumes/{CATALOG}/{LANDING}/{VOLUME}"

ENTITIES = [
    "customer", "rate_plan", "subscription", "contract", "promotion",
    "subscription_promotion", "invoice", "invoice_line", "payment", "usage_summary",
]

# primary keys (for silver dedup)
PK = {
    "customer": ["customer_id"],
    "rate_plan": ["plan_id"],
    "subscription": ["subscription_id"],
    "contract": ["contract_id"],
    "promotion": ["promo_id"],
    "subscription_promotion": ["sub_promo_id"],
    "invoice": ["invoice_id"],
    "invoice_line": ["invoice_line_id"],
    "payment": ["payment_id"],
    "usage_summary": ["subscription_id", "billing_period"],
}


# genie
GENIE_SPACE_TITLE = "AcmeTel Billing Assistant"

# agent (ML/GenAI)
LLM_ENDPOINT = "databricks-claude-sonnet-4-5"
AGENT_MODEL_NAME = "acmetel_billing_agent"      # registered under CATALOG.GOLD
AGENT_ENDPOINT = "acmetel-billing-agent"

# app
APP_NAME = "acmetel-billing-360"

# lakebase (agent context/memory layer)
LAKEBASE_PROJECT = "acmetel"
LAKEBASE_MEMORY_SCHEMA = "acmetel_memory"
EMBEDDING_ENDPOINT = "databricks-gte-large-en"
EMBEDDING_DIMS = 1024


def t(schema, name):
    return f"{CATALOG}.{schema}.{name}"
