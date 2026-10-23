# Databricks notebook source
# MAGIC %pip install --quiet "databricks-sdk>=0.81.0"
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %run ./config

# COMMAND ----------
import json, uuid
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
G = f"{CATALOG}.{GOLD}"
def hid():
    return uuid.uuid4().hex

# discover a serverless PRO SQL warehouse (Genie rejects classic and realtime)
WAREHOUSE_ID = sorted((x for x in w.warehouses.list() if x.warehouse_type and x.warehouse_type.value == "PRO"),
                      key=lambda x: (not x.enable_serverless_compute, x.state.value != "RUNNING"))[0].id

# COMMAND ----------
# tables + metric views (sorted by identifier — API requirement)
tables = [{"identifier": f"{G}.{e}"} for e in ENTITIES + METRIC_VIEWS]
tables = sorted(tables, key=lambda x: x["identifier"])

# sample questions (UI bubbles)
sample_qs = [
    "Why did my bill go up this month?",
    "Is my discount still active?",
    "How much do I owe and how many days overdue am I?",
    "When does my contract end and what is the early termination fee?",
    "Did I exceed my data plan last month?",
    "What is the ARPU trend by month?",
    "How much revenue is at risk from customers 60+ days delinquent?",
]
sample_questions = sorted([{"id": hid(), "question": [q]} for q in sample_qs], key=lambda x: x["id"])

# COMMAND ----------
# thin instructions — UC table/column comments are auto-read by Genie
instr = (
    "You are the billing assistant for AcmeTel, a LATAM telecom operator. "
    "Answer end-customer billing questions (invoices, discounts, overage, contracts, plan changes) "
    "and internal analytics (ARPU, collection rate, revenue at risk).\n"
    "- 'Today' is current_date().\n"
    "- invoice.status: paid | partial | overdue | unpaid. payment.dunning_stage: 0=current,1=1-30d,2=31-60d,3=61-90d,4=>90d.\n"
    "- For 'why did my bill go up', break down invoice_line by charge_type for the last two billing periods and name the cause "
    "(expired discount, new overage, device installment, one-time charge).\n"
    "- Use the mv_* metric views for aggregated KPIs; use raw tables for customer-specific detail.\n"
    "- Collection rate = share of invoices paid (mv_collection_rate), not a dollar ratio. Days overdue = days since the "
    "oldest unpaid due date, as returned by get_payment_status.\n"
    "- Be concise, don't restate the question, and answer in the language of the question (default English)."
)
text_instructions = [{"id": hid(), "content": [instr]}]

# COMMAND ----------
# example question -> SQL pairs (few-shot teaching), sorted by id
def ex(question, sql):
    return {"id": hid(), "question": [question], "sql": [sql]}

examples = [
    ex("Why did customer CUS-000002's bill increase this month?",
       f"SELECT i.billing_period, il.charge_type, il.description, il.amount "
       f"FROM {G}.invoice i JOIN {G}.invoice_line il ON i.invoice_id = il.invoice_id "
       f"WHERE i.customer_id = 'CUS-000002' "
       f"AND i.billing_period >= date_format(add_months(current_date(), -1), 'yyyy-MM') "
       f"ORDER BY i.billing_period DESC, il.amount DESC"),
    ex("Is the discount for customer CUS-000002 still active?",
       f"SELECT * FROM {G}.check_discount_status('CUS-000002')"),
    ex("How much does customer CUS-000002 owe and how overdue are they?",
       f"SELECT * FROM {G}.get_payment_status('CUS-000002')"),
    ex("Recommend a better plan for customer CUS-000002 based on usage.",
       f"SELECT * FROM {G}.get_next_best_offer('CUS-000002')"),
    ex("What is the monthly ARPU trend?",
       f"SELECT billing_period, MEASURE(arpu) AS arpu, MEASURE(total_revenue) AS revenue "
       f"FROM {G}.mv_arpu_monthly GROUP BY billing_period ORDER BY billing_period"),
    ex("What is the collection rate this month by segment?",
       f"SELECT segment, MEASURE(collection_rate) AS collection_rate, MEASURE(paid_invoices) AS paid, "
       f"MEASURE(total_invoices) AS total FROM {G}.mv_collection_rate "
       f"WHERE billing_period = (SELECT MAX(billing_period) FROM {G}.invoice) GROUP BY segment ORDER BY collection_rate"),
    ex("How much revenue is at risk from customers 60+ days delinquent?",
       f"SELECT MEASURE(revenue_at_risk) AS revenue_at_risk, MEASURE(customers_at_risk) AS customers "
       f"FROM {G}.mv_revenue_at_risk"),
]
example_question_sqls = sorted(examples, key=lambda x: x["id"])

# COMMAND ----------
# join specs (short table names in SQL + relationship-type marker), sorted by id
def join(a, b, on, comment):
    return {"id": hid(), "left": {"identifier": f"{G}.{a}"}, "right": {"identifier": f"{G}.{b}"},
            "sql": [on, "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"], "comment": [comment]}

joins = [
    join("subscription", "customer", "subscription.customer_id = customer.customer_id", "Subscription belongs to a customer"),
    join("subscription", "rate_plan", "subscription.plan_id = rate_plan.plan_id", "Subscription uses a plan"),
    join("contract", "subscription", "contract.subscription_id = subscription.subscription_id", "Contract ties to a subscription"),
    join("subscription_promotion", "subscription", "subscription_promotion.subscription_id = subscription.subscription_id", "Promotion applies to a subscription"),
    join("subscription_promotion", "promotion", "subscription_promotion.promo_id = promotion.promo_id", "References the promotion"),
    join("invoice", "customer", "invoice.customer_id = customer.customer_id", "Invoice belongs to a customer"),
    join("invoice_line", "invoice", "invoice_line.invoice_id = invoice.invoice_id", "Line item belongs to an invoice"),
    join("payment", "invoice", "payment.invoice_id = invoice.invoice_id", "Payment settles an invoice"),
    join("usage_summary", "subscription", "usage_summary.subscription_id = subscription.subscription_id", "Usage tracked per subscription"),
]
join_specs = sorted(joins, key=lambda x: x["id"])

# COMMAND ----------
# assemble + serialize
serialized_space = json.dumps({
    "version": 2,
    "data_sources": {"tables": tables},
    "config": {"sample_questions": sample_questions},
    "instructions": {
        "text_instructions": text_instructions,
        "example_question_sqls": example_question_sqls,
        "join_specs": join_specs,
    },
}, ensure_ascii=False)

# COMMAND ----------
# idempotent create/update by title
existing = next((s for s in w.genie.list_spaces().spaces or [] if s.title == GENIE_SPACE_TITLE), None)
DESC = "Natural-language billing assistant over the AcmeTel gold model (invoices, discounts, dunning, plans)."
if existing:
    sp = w.genie.update_space(existing.space_id, serialized_space=serialized_space,
                              title=GENIE_SPACE_TITLE, description=DESC, warehouse_id=WAREHOUSE_ID)
    print(f"updated Genie space: {sp.space_id}")
else:
    sp = w.genie.create_space(warehouse_id=WAREHOUSE_ID, serialized_space=serialized_space,
                              title=GENIE_SPACE_TITLE, description=DESC)
    print(f"created Genie space: {sp.space_id}")

print("space_id:", sp.space_id)
print("tables:", len(tables), "| examples:", len(example_question_sqls), "| joins:", len(join_specs))
