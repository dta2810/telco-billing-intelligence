# Databricks notebook source
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

n_gold = cnt(f"SELECT count(*) FROM {CATALOG}.information_schema.tables WHERE table_schema='{GOLD}'")
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
    <h2 style="margin:0">AcmeTel — Part 1 validation</h2>
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
