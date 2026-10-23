# Databricks notebook source
# MAGIC %pip install --quiet "databricks-sdk>=0.81.0" "psycopg>=3.0"
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %run ./config

# COMMAND ----------
def cnt(sql):
    return spark.sql(sql).collect()[0][0]

def rf(e):
    return f"read_files('{VOL_PATH}/{e}', format=>'csv', header=>true, inferSchema=>true)"

checks = []
def check(group, name, actual, ok, detail=""):
    checks.append((group, name, actual, bool(ok), detail))

# COMMAND ----------
# structure checks
n_schemas = cnt(f"SELECT count(*) FROM {CATALOG}.information_schema.schemata WHERE schema_name LIKE 'acmetel_%'")
check("Unity Catalog", "medallion schemas", n_schemas, n_schemas == 4, "landing/bronze/silver/gold")

n_gold = cnt(f"SELECT count(*) FROM {CATALOG}.information_schema.tables WHERE table_schema='{GOLD}' AND table_type='MANAGED'")
check("Unity Catalog", "gold tables", n_gold, n_gold == 10)

n_comment = cnt(f"SELECT count(*) FROM {CATALOG}.information_schema.columns WHERE table_schema='{GOLD}' AND comment IS NOT NULL")
check("Unity Catalog", "gold columns with comment", n_comment, n_comment > 0, "UC context layer")

# COMMAND ----------
# raw landing counts
EXPECT = {"customer": 300, "rate_plan": 10, "promotion": 15, "subscription_promotion": 500,
          "invoice": 1800, "payment": 1500, "usage_summary": 1600}
for e in ENTITIES:
    c = cnt(f"SELECT count(*) FROM {rf(e)}")
    exp = EXPECT.get(e)
    check("Landing (raw)", e, c, c == exp if exp else c > 0, f"expected {exp}" if exp else "")

# COMMAND ----------
# seeded business scenarios
s1 = cnt(f"SELECT count(*) FROM {rf('subscription_promotion')} WHERE status='expired'")
check("Scenarios", "expired discounts", s1, s1 > 0)
s2 = cnt(f"SELECT count(*) FROM {rf('payment')} WHERE dunning_stage>=1")
check("Scenarios", "delinquent payments (dunning>=1)", s2, s2 > 0)
s3 = cnt(f"SELECT count(*) FROM {rf('invoice')} WHERE status='overdue'")
check("Scenarios", "overdue invoices", s3, s3 > 0)
s4 = cnt(f"SELECT count(*) FROM {rf('usage_summary')} WHERE data_overage_mb>0")
check("Scenarios", "usage rows with overage", s4, s4 > 0)

# COMMAND ----------
# medallion layer parity: bronze = silver = gold, populated
for e in ENTITIES:
    b = spark.table(t(BRONZE, e)).count()
    s = spark.table(t(SILVER, e)).count()
    g = spark.table(t(GOLD, e)).count()
    check("Medallion layers", e, f"{b}/{s}/{g}", b == s == g and g > 0, "bronze/silver/gold")

# COMMAND ----------
# metric views (semantic layer)
n_mv = cnt(f"SELECT count(*) FROM {CATALOG}.information_schema.tables WHERE table_schema='{GOLD}' AND table_type='METRIC_VIEW'")
check("Semantic layer", "metric views", n_mv, n_mv == 8)

# COMMAND ----------
# lakebase context/memory layer (query Postgres directly)
try:
    import psycopg
    from databricks.sdk import WorkspaceClient
    _w = WorkspaceClient()
    _branch = dbutils.widgets.get("lakebase_branch") if "lakebase_branch" in [x.name for x in dbutils.widgets.getAll()] else "production"
    _ep = f"projects/{LAKEBASE_PROJECT}/branches/{_branch}/endpoints/primary"
    _host = _w.postgres.get_endpoint(name=_ep).status.hosts.host
    _tok = _w.postgres.generate_database_credential(endpoint=_ep).token
    _user = _w.current_user.me().user_name
    _c = psycopg.connect(host=_host, dbname="databricks_postgres", user=_user,
                         password=_tok, sslmode="require")
    with _c.cursor() as _cur:
        _cur.execute(f"SELECT count(*) FROM pg_tables WHERE schemaname='{LAKEBASE_MEMORY_SCHEMA}'")
        n_tbl = _cur.fetchone()[0]
        _cur.execute("SELECT count(*) FROM pg_extension WHERE extname='vector'")
        has_vec = _cur.fetchone()[0]
    _c.close()
    check("Lakebase memory", f"memory tables (branch={_branch})", n_tbl, n_tbl >= 6, LAKEBASE_MEMORY_SCHEMA)
    check("Lakebase memory", "pgvector extension", has_vec, has_vec == 1)
except Exception as e:
    check("Lakebase memory", "reachable", str(e)[:40], False, "run 07_lakebase_setup first")

# COMMAND ----------
# genie room (live NL -> SQL over gold)
try:
    import time
    from databricks.sdk import WorkspaceClient
    _w = WorkspaceClient()
    _sp = next((s for s in _w.genie.list_spaces().spaces or [] if s.title == GENIE_SPACE_TITLE), None)
    if not _sp:
        check("Genie room", "space exists", "missing", False, GENIE_SPACE_TITLE)
    else:
        _conv = _w.genie.start_conversation_and_wait(
            _sp.space_id, "How much revenue is at risk from customers 60+ days delinquent?")
        _atts = _conv.attachments or []
        _sql = next((a.query.query for a in _atts if a.query), None)
        _txt = next((a.text.content for a in _atts if a.text), None)
        check("Genie room", "NL->SQL answered", "yes" if (_sql or _txt) else "no", bool(_sql or _txt),
              (_sql or _txt or "")[:60].replace("\n", " "))
except Exception as e:
    check("Genie room", "reachable", str(e)[:40], False, "run 12_genie first")

# COMMAND ----------
# databricks app (status + live API endpoints)
try:
    import urllib.request
    from databricks.sdk import WorkspaceClient
    _w = WorkspaceClient()
    _app = _w.apps.get(name=APP_NAME)
    _state = _app.app_status.state.value if (_app.app_status and _app.app_status.state) else "?"
    check("Databricks app", "app running", _state, _state == "RUNNING", f"{APP_NAME} · {_app.url or ''}")
    # Live API endpoints (/api/health, /api/smoke) are verified separately with an OAuth token
    # (see evidence/part5_app.md) — app auth from inside a job is not reliable, so not asserted here.
except Exception as e:
    check("Databricks app", "app running", str(e)[:40], False, "run 14_app first")

# COMMAND ----------
# render HTML report
passed = sum(1 for *_, ok, _ in checks if ok)
total = len(checks)
rows = ""
last_group = None
for group, name, actual, ok, detail in checks:
    if group != last_group:
        rows += f"<tr><td colspan=4 style='padding:10px 12px;background:#f1f3f5;font-weight:600'>{group}</td></tr>"
        last_group = group
    badge = "#1a7f37" if ok else "#cf222e"
    label = "PASS" if ok else "FAIL"
    rows += (f"<tr style='border-bottom:1px solid #eaecef'>"
             f"<td style='padding:8px 12px'>{name}</td>"
             f"<td style='padding:8px 12px;text-align:right;font-variant-numeric:tabular-nums'>{actual}</td>"
             f"<td style='padding:8px 12px;color:#57606a'>{detail}</td>"
             f"<td style='padding:8px 12px'><span style='background:{badge};color:#fff;border-radius:10px;padding:2px 10px;font-size:12px'>{label}</span></td>"
             f"</tr>")
overall = "#1a7f37" if passed == total else "#cf222e"
html = f"""
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:760px">
  <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
    <h2 style="margin:0">AcmeTel — end-to-end validation</h2>
    <span style="background:{overall};color:#fff;border-radius:12px;padding:4px 12px;font-weight:600">{passed}/{total} passed</span>
  </div>
  <div style="color:#57606a;margin-bottom:12px">Catalog <code>{CATALOG}</code> · landing volume <code>{VOL_PATH}</code></div>
  <table style="border-collapse:collapse;width:100%;border:1px solid #d0d7de;border-radius:8px;overflow:hidden">
    <thead><tr style="background:#24292f;color:#fff;text-align:left">
      <th style="padding:8px 12px">Check</th><th style="padding:8px 12px;text-align:right">Value</th>
      <th style="padding:8px 12px">Detail</th><th style="padding:8px 12px">Status</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""
displayHTML(html)

# COMMAND ----------
# text summary (evidence)
print(f"VALIDATION {passed}/{total} passed")
for group, name, actual, ok, detail in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {group:14s} {name:34s} {actual}  {detail}")

# COMMAND ----------
# representative data samples (evidence — real rows, capped with LIMIT). Each block guarded
# so a sample never fails the validation run.
def sample(title, sql):
    print(f"\n=== {title} ===")
    try:
        spark.sql(sql).show(truncate=False)
    except Exception as e:
        print("sample skipped:", str(e)[:120])

sample("gold.customer (sample)",
       f"SELECT customer_id, full_name, segment, status FROM {t(GOLD,'customer')} LIMIT 5")
sample("ARPU trend by period (mv_arpu_monthly)",
       f"""SELECT billing_period, MEASURE(arpu) AS arpu, MEASURE(total_revenue) AS revenue
           FROM {t(GOLD,'mv_arpu_monthly')} GROUP BY billing_period ORDER BY billing_period""")
sample("revenue at risk (mv_revenue_at_risk)",
       f"""SELECT MEASURE(revenue_at_risk) AS revenue_at_risk, MEASURE(customers_at_risk) AS customers
           FROM {t(GOLD,'mv_revenue_at_risk')}""")
sample("UC function get_payment_status('CUS-000002') — delinquent persona",
       f"SELECT * FROM {t(GOLD,'get_payment_status')}('CUS-000002')")
sample("UC function check_discount_status('CUS-000002')",
       f"SELECT status, promo_name, days_to_expire, reason FROM {t(GOLD,'check_discount_status')}('CUS-000002')")

# COMMAND ----------
# representative Genie answer (text)
try:
    if _sp:
        print("=== Genie NL->SQL (representative) ===")
        print("Q: How much revenue is at risk from customers 60+ days delinquent?")
        print("SQL:", (_sql or "")[:300])
        print("A:", (_txt or "")[:400])
except Exception:
    print("Genie sample skipped")
