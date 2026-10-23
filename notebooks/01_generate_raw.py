# Databricks notebook source
# MAGIC %pip install faker

# COMMAND ----------
# MAGIC %run ./config

# COMMAND ----------
import os, random
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd
from faker import Faker

SEED = 42
random.seed(SEED)
Faker.seed(SEED)
fake = Faker("es_MX")

TODAY = date.today()
def _month_back(d, n):
    y, m = d.year, d.month - n
    while m <= 0:
        y -= 1; m += 12
    return date(y, m, 1)
PERIODS_DT = [_month_back(TODAY, i) for i in range(6)][::-1]
PERIODS = [d.strftime("%Y-%m") for d in PERIODS_DT]

def cid(i):  return f"CUS-{i:06d}"
def sid(i):  return f"SUB-{i:06d}"
def ctid(i): return f"CT-{i:06d}"
def spid(i): return f"SP-{i:06d}"
def iid(i):  return f"INV-{i:07d}"
def ilid(i): return f"IL-{i:08d}"
def payid(i):return f"PAY-{i:07d}"

# COMMAND ----------
# rate_plan (10 plans)
plans = [
    ("PLAN-001", "AcmeTel Lite 5GB",      14.99,   5, 200, 100, 6.00, date(2024,1,1), None),
    ("PLAN-002", "AcmeTel Std 10GB",      22.99,  10, 500, 200, 5.00, date(2024,1,1), None),
    ("PLAN-003", "AcmeTel Pro 30GB",      34.99,  30,  -1,  -1, 4.00, date(2024,1,1), None),
    ("PLAN-004", "AcmeTel Premium 100GB", 54.99, 100,  -1,  -1, 3.00, date(2024,1,1), None),
    ("PLAN-005", "AcmeTel Family 60GB",   64.99,  60,  -1,  -1, 4.00, date(2024,1,1), None),
    ("PLAN-006", "AcmeTel Pro 50GB",      44.99,  50,  -1,  -1, 4.00, date(2025,6,1), None),
    ("PLAN-007", "AcmeTel Smart 20GB",    29.99,  20, 500, 300, 5.00, date(2025,1,1), None),
    ("PLAN-008", "AcmeTel Legacy 3GB",     9.99,   3, 100,  50, 8.00, date(2022,1,1), date(2024,12,31)),
    ("PLAN-009", "AcmeTel Legacy 8GB",    19.99,   8, 300, 150, 6.00, date(2022,1,1), date(2024,12,31)),
    ("PLAN-010", "AcmeTel Old 15GB",      24.99,  15, 400, 200, 5.50, date(2023,1,1), date(2025,6,30)),
]
df_plan = pd.DataFrame(plans, columns=[
    "plan_id","plan_name","monthly_fee","data_quota_gb","voice_minutes",
    "sms_quota","data_overage_per_gb","valid_from","valid_to"])
ACTIVE_PLANS  = df_plan[df_plan.valid_to.isna()]["plan_id"].tolist()
PLAN_FEE      = dict(zip(df_plan.plan_id, df_plan.monthly_fee))
PLAN_QUOTA_GB = dict(zip(df_plan.plan_id, df_plan.data_quota_gb))
PLAN_NAME     = dict(zip(df_plan.plan_id, df_plan.plan_name))
PLAN_OVERAGE_RATE = dict(zip(df_plan.plan_id, df_plan.data_overage_per_gb))

# COMMAND ----------
# customer (300)
N_CUSTOMERS = 300
SEGMENTS = ["consumer"]*240 + ["smb"]*45 + ["enterprise"]*15
random.shuffle(SEGMENTS)
cust_rows = []
for i in range(1, N_CUSTOMERS+1):
    cust_rows.append({
        "customer_id":    cid(i),
        "full_name":      fake.name(),
        "tax_id":         f"{random.randint(10000000, 99999999)}",
        "segment":        SEGMENTS[i-1],
        "status":         random.choices(["active","suspended","churned"], weights=[92,5,3])[0],
        "signup_date":    TODAY - timedelta(days=random.randint(60, 1500)),
        "email":          fake.email(),
        "msisdn_primary": f"+507{random.randint(60000000, 69999999)}",
    })
df_cust = pd.DataFrame(cust_rows)

# COMMAND ----------
# subscription (~375)
sub_rows, sub_counter = [], 0
for c in df_cust.itertuples():
    for _ in range(2 if random.random() < 0.25 else 1):
        sub_counter += 1
        plan = random.choice(ACTIVE_PLANS)
        device_subsidy = round(random.uniform(0, 600), 2) if random.random() < 0.3 else 0.0
        sub_rows.append({
            "subscription_id":       sid(sub_counter),
            "customer_id":           c.customer_id,
            "plan_id":               plan,
            "msisdn":                f"+507{random.randint(60000000, 69999999)}",
            "activation_date":       c.signup_date + timedelta(days=random.randint(0, 60)),
            "status":                "active" if c.status=="active" else random.choice(["active","suspended","terminated"]),
            "device_imei":           f"35{random.randint(10**13, 10**14-1)}" if random.random()<0.7 else None,
            "device_subsidy_amount": device_subsidy,
        })
df_sub = pd.DataFrame(sub_rows)

# COMMAND ----------
# contract (1:1 with subscription; 10% expiring within 60d)
contract_rows = []
for i, s in enumerate(df_sub.itertuples(), 1):
    term = random.choice([12, 18, 24])
    signed = s.activation_date
    end = signed + timedelta(days=term*30)
    if random.random() < 0.10:
        end = TODAY + timedelta(days=random.randint(1, 60))
        signed = end - timedelta(days=term*30)
    contract_rows.append({
        "contract_id":           ctid(i),
        "customer_id":           s.customer_id,
        "subscription_id":       s.subscription_id,
        "signed_date":           signed,
        "term_months":           term,
        "end_date":              end,
        "early_termination_fee": round(random.uniform(50, 300), 2),
        "auto_renew":            random.random() < 0.6,
        "status":                "active" if end >= TODAY else "expired",
    })
df_contract = pd.DataFrame(contract_rows)

# COMMAND ----------
# promotion (15)
promos = [
    ("PROMO-001","Loyalty Discount 20%",       "percent",      20.00, 12, "Customers with >24 months tenure"),
    ("PROMO-002","Welcome 50% First Month",     "percent",      50.00,  1, "New customers first month"),
    ("PROMO-003","10GB Extra Free",             "free_data",    10.00,  6, "Summer 2025 promo"),
    ("PROMO-004","Family Discount 15%",         "percent",      15.00, 24, "Customers with 2+ active lines"),
    ("PROMO-005","$5 OFF Monthly",              "fixed_amount",  5.00,  6, "Auto-pay enabled"),
    ("PROMO-006","Free Device",                 "fixed_amount", 30.00, 24, "Renewal with Premium plan"),
    ("PROMO-007","Free Caribbean Roaming",      "free_data",     5.00,  3, "Summer 2025"),
    ("PROMO-008","Black Friday 30%",            "percent",      30.00,  3, "Black Friday 2025"),
    ("PROMO-009","Student 25% OFF",             "percent",      25.00, 12, "Student ID verification"),
    ("PROMO-010","Senior 30%",                  "percent",      30.00, 24, "Ages 65+"),
    ("PROMO-011","Pro Upgrade 2x1",             "fixed_amount", 12.99,  6, "Upgrade from Std to Pro"),
    ("PROMO-012","Referral $10 OFF",            "fixed_amount", 10.00,  3, "Per active referral"),
    ("PROMO-013","Prepay 12% OFF",              "percent",      12.00, 12, "12 months paid upfront"),
    ("PROMO-014","Internet+Mobile Bundle 18%",  "percent",      18.00, 24, "Bundled with fixed internet"),
    ("PROMO-015","Carrier Migration",           "fixed_amount",  8.00,  6, "Number portability from another carrier"),
]
df_promo = pd.DataFrame(promos, columns=[
    "promo_id","promo_name","discount_type","discount_value","duration_months","eligibility_rule"])
PROMO_VAL  = dict(zip(df_promo.promo_id, df_promo.discount_value))
PROMO_TYPE = dict(zip(df_promo.promo_id, df_promo.discount_type))
PROMO_DUR  = dict(zip(df_promo.promo_id, df_promo.duration_months))

# COMMAND ----------
# subscription_promotion (500) — 15% of customers have a discount that expired last month
N_SUB_PROMO = 500
sub_ids = df_sub["subscription_id"].tolist()
EXPIRED_LAST_MONTH = set(random.sample(df_cust["customer_id"].tolist(), int(N_CUSTOMERS*0.15)))
last_month_end = TODAY.replace(day=1) - timedelta(days=1)
sp_rows, sp_counter = [], 0
for cust_id in EXPIRED_LAST_MONTH:
    sub_for_cust = df_sub[df_sub.customer_id==cust_id]["subscription_id"].iloc[0]
    promo = random.choice(df_promo["promo_id"].tolist())
    end_d = last_month_end - timedelta(days=random.randint(0, 25))
    start_d = end_d - timedelta(days=PROMO_DUR[promo]*30)
    sp_counter += 1
    sp_rows.append({"sub_promo_id": spid(sp_counter), "subscription_id": sub_for_cust,
                    "promo_id": promo, "start_date": start_d, "end_date": end_d, "status": "expired"})
while sp_counter < N_SUB_PROMO:
    sub = random.choice(sub_ids)
    promo = random.choice(df_promo["promo_id"].tolist())
    start_d = TODAY - timedelta(days=random.randint(-180, 540))
    end_d = start_d + timedelta(days=PROMO_DUR[promo]*30)
    if end_d < TODAY:
        status = "expired"
    elif random.random() < 0.05:
        status = "cancelled"
    else:
        status = "active"
    sp_counter += 1
    sp_rows.append({"sub_promo_id": spid(sp_counter), "subscription_id": sub,
                    "promo_id": promo, "start_date": start_d, "end_date": end_d, "status": status})
df_sub_promo = pd.DataFrame(sp_rows)

# COMMAND ----------
# invoice + invoice_line (6 months × customers)
CUST_SUBS = df_sub.groupby("customer_id")["subscription_id"].apply(list).to_dict()
SUB_PLAN  = dict(zip(df_sub.subscription_id, df_sub.plan_id))
SUB_DEVICE_SUB = dict(zip(df_sub.subscription_id, df_sub.device_subsidy_amount))
SUB_PROMOS = {}
for r in df_sub_promo.itertuples():
    SUB_PROMOS.setdefault(r.subscription_id, []).append((r.promo_id, r.start_date, r.end_date))
ONE_TIME_CUSTOMERS = set(random.sample(df_cust.customer_id.tolist(), max(1, int(N_CUSTOMERS*0.05))))
ONE_TIME_PERIOD = {c: random.choice(PERIODS) for c in ONE_TIME_CUSTOMERS}
INVOICES_TO_PATCH_OVERAGE = []

inv_rows, line_rows, inv_counter, line_counter = [], [], 0, 0
for c in df_cust.itertuples():
    subs = CUST_SUBS.get(c.customer_id, [])
    if not subs: continue
    for period_dt in PERIODS_DT:
        period_str = period_dt.strftime("%Y-%m")
        issue = period_dt.replace(day=5)
        due = issue + timedelta(days=15)
        subtotal, discount_total = Decimal("0"), Decimal("0")
        inv_counter += 1
        invoice_id = iid(inv_counter)
        for sub in subs:
            plan = SUB_PLAN[sub]
            fee = Decimal(str(PLAN_FEE[plan]))
            subtotal += fee
            line_counter += 1
            line_rows.append({"invoice_line_id": ilid(line_counter), "invoice_id": invoice_id,
                "subscription_id": sub, "charge_type": "recurring",
                "description": f"{PLAN_NAME[plan]} - {period_str}", "amount": float(fee)})
            sub_amt = SUB_DEVICE_SUB[sub]
            if sub_amt and sub_amt > 0:
                cuota = round(min(float(sub_amt)/12, 50.0), 2)
                subtotal += Decimal(str(cuota))
                line_counter += 1
                line_rows.append({"invoice_line_id": ilid(line_counter), "invoice_id": invoice_id,
                    "subscription_id": sub, "charge_type": "device_subsidy",
                    "description": f"Device installment - {period_str}", "amount": cuota})
            if c.customer_id in ONE_TIME_CUSTOMERS and ONE_TIME_PERIOD[c.customer_id]==period_str and sub==subs[0]:
                kind = random.choice(["device_sale","activation","late_fee"])
                if kind == "device_sale":
                    desc, amt = "Device purchase (one-time)", Decimal(str(round(random.uniform(150,800),2)))
                elif kind == "activation":
                    desc, amt = "One-time activation fee", Decimal("15.00")
                else:
                    desc, amt = "Late fee from prior period", Decimal(str(round(random.uniform(2,8),2)))
                subtotal += amt
                line_counter += 1
                line_rows.append({"invoice_line_id": ilid(line_counter), "invoice_id": invoice_id,
                    "subscription_id": sub, "charge_type": "one_time", "description": desc, "amount": float(amt)})
            INVOICES_TO_PATCH_OVERAGE.append((invoice_id, sub, period_str, plan))
            for promo_id, sp_start, sp_end in SUB_PROMOS.get(sub, []):
                if sp_start <= period_dt <= sp_end:
                    pv, pt = Decimal(str(PROMO_VAL[promo_id])), PROMO_TYPE[promo_id]
                    if pt == "percent":
                        d_amt = (fee * pv / Decimal("100")).quantize(Decimal("0.01"))
                    elif pt == "fixed_amount":
                        d_amt = pv
                    else:
                        d_amt = Decimal("0")
                    if d_amt > 0:
                        discount_total += d_amt
                        line_counter += 1
                        line_rows.append({"invoice_line_id": ilid(line_counter), "invoice_id": invoice_id,
                            "subscription_id": sub, "charge_type": "discount",
                            "description": f"Discount applied - {period_str}", "amount": -float(d_amt)})
        tax = ((subtotal - discount_total) * Decimal("0.07")).quantize(Decimal("0.01"))
        if tax > 0:
            line_counter += 1
            line_rows.append({"invoice_line_id": ilid(line_counter), "invoice_id": invoice_id,
                "subscription_id": subs[0], "charge_type": "tax",
                "description": f"VAT 7% - {period_str}", "amount": float(tax)})
        total_due = subtotal - discount_total + tax
        inv_rows.append({"invoice_id": invoice_id, "customer_id": c.customer_id, "billing_period": period_str,
            "issue_date": issue, "due_date": due, "subtotal": float(subtotal.quantize(Decimal("0.01"))),
            "discount_amount": float(discount_total.quantize(Decimal("0.01"))), "tax_amount": float(tax),
            "total_due": float(total_due.quantize(Decimal("0.01"))), "status": "paid"})
df_inv = pd.DataFrame(inv_rows)

# COMMAND ----------
# payment (1500) + dunning seeding (12% stage 1, 5% stage 3), stage aligned with days overdue
N_PAYMENTS_TARGET = 1500
mora_pool = df_cust["customer_id"].tolist()
random.shuffle(mora_pool)
n1, n3 = int(N_CUSTOMERS*0.12), int(N_CUSTOMERS*0.05)
MORA_1_CUSTS = set(mora_pool[:n1])
MORA_3_CUSTS = set(mora_pool[n1:n1+n3])

# stage 3 cohort: unpaid since the latest due date 61+ days ago; stage 1 cohort: latest past due date unpaid
def _stage(age):
    return 1 if age <= 30 else 2 if age <= 60 else 3 if age <= 90 else 4

OLDEST_UNPAID = {}
for cust in MORA_3_CUSTS:
    dues = [d for d in df_inv.loc[df_inv.customer_id == cust, "due_date"] if (TODAY - d).days >= 61]
    if dues: OLDEST_UNPAID[cust] = max(dues)
for cust in MORA_1_CUSTS:
    dues = [d for d in df_inv.loc[df_inv.customer_id == cust, "due_date"] if (TODAY - d).days >= 1]
    if dues: OLDEST_UNPAID[cust] = max(dues)

def _unpaid_stage(cust, due):
    oldest = OLDEST_UNPAID.get(cust)
    if oldest and oldest <= due < TODAY:
        return _stage((TODAY - oldest).days)
    return None

pay_rows = []
for inv in df_inv.sort_values(["customer_id","billing_period"]).itertuples():
    stage = _unpaid_stage(inv.customer_id, inv.due_date)
    if stage:
        pay_rows.append({"invoice_id": inv.invoice_id, "customer_id": inv.customer_id,
            "payment_date": None, "amount": 0.0, "method": random.choice(["card","app","bank_transfer"]),
            "status": "pending", "dunning_stage": stage})
        df_inv.loc[df_inv.invoice_id==inv.invoice_id, "status"] = "overdue"
        continue
    pay_rows.append({"invoice_id": inv.invoice_id, "customer_id": inv.customer_id,
        "payment_date": inv.due_date - timedelta(days=random.randint(0,5)), "amount": inv.total_due,
        "method": random.choices(["card","app","bank_transfer","cash"], weights=[55,25,15,5])[0],
        "status": "success", "dunning_stage": 0})

# keep every dunning row, sample paid rows up to the target
mora_rows = [r for r in pay_rows if r["dunning_stage"] > 0]
paid_rows = random.sample([r for r in pay_rows if r["dunning_stage"] == 0], N_PAYMENTS_TARGET - len(mora_rows))
df_pay = pd.DataFrame(sorted(mora_rows + paid_rows, key=lambda r: (r["customer_id"], r["invoice_id"])))
df_pay.insert(0, "payment_id", [payid(i + 1) for i in range(len(df_pay))])

# COMMAND ----------
# usage_summary (1600) — 18% of subs with relevant overage
N_USAGE = 1600
overage_subs = set(random.sample(df_sub.subscription_id.tolist(), int(len(df_sub)*0.18)))
usage_rows = []
for sub_row in df_sub.itertuples():
    quota_mb = PLAN_QUOTA_GB[SUB_PLAN[sub_row.subscription_id]] * 1024
    for period in PERIODS:
        if sub_row.subscription_id in overage_subs and random.random() < 0.6:
            overage_mb = random.randint(2048, 8192)
            data_used = quota_mb + overage_mb
        else:
            overage_mb = 0
            data_used = random.randint(int(quota_mb*0.2), quota_mb-100)
        usage_rows.append({"subscription_id": sub_row.subscription_id, "billing_period": period,
            "voice_minutes_used": random.randint(0,800), "data_mb_used": data_used,
            "sms_count": random.randint(0,200), "data_overage_mb": overage_mb,
            "roaming_data_mb": random.randint(0,500) if random.random()<0.05 else 0})
        if len(usage_rows) >= N_USAGE: break
    if len(usage_rows) >= N_USAGE: break
df_usage = pd.DataFrame(usage_rows)

# COMMAND ----------
# patch invoice_line with usage_overage rows, then adjust invoice totals
USAGE_LOOKUP = {(r.subscription_id, r.billing_period): int(r.data_overage_mb)
                for r in df_usage.itertuples() if int(r.data_overage_mb) > 0}
inv_to_extra = {}
for invoice_id, sub, period_str, plan in INVOICES_TO_PATCH_OVERAGE:
    overage_mb = USAGE_LOOKUP.get((sub, period_str), 0)
    if overage_mb <= 0: continue
    overage_gb = round(overage_mb / 1024.0, 2)
    rate = float(PLAN_OVERAGE_RATE.get(plan, 5.0))
    charge = round(overage_gb * rate, 2)
    if charge < 0.01: continue
    line_counter += 1
    line_rows.append({"invoice_line_id": ilid(line_counter), "invoice_id": invoice_id, "subscription_id": sub,
        "charge_type": "usage_overage",
        "description": f"Data overage {overage_gb} GB x ${rate:.2f}/GB - {period_str}", "amount": charge})
    inv_to_extra[invoice_id] = inv_to_extra.get(invoice_id, 0.0) + charge
if inv_to_extra:
    extra_df = pd.DataFrame([{"invoice_id": k, "extra": v} for k, v in inv_to_extra.items()])
    df_inv = df_inv.merge(extra_df, on="invoice_id", how="left").fillna({"extra": 0.0})
    df_inv["subtotal"]   = (df_inv["subtotal"] + df_inv["extra"]).round(2)
    extra_tax            = (df_inv["extra"] * 0.07).round(2)
    df_inv["tax_amount"] = (df_inv["tax_amount"] + extra_tax).round(2)
    df_inv["total_due"]  = (df_inv["total_due"] + df_inv["extra"] + extra_tax).round(2)
    df_inv = df_inv.drop(columns=["extra"])
df_line = pd.DataFrame(line_rows)

# COMMAND ----------
# write raw CSV per entity to the landing volume
DATASETS = {
    "customer": df_cust, "rate_plan": df_plan, "subscription": df_sub, "contract": df_contract,
    "promotion": df_promo, "subscription_promotion": df_sub_promo, "invoice": df_inv,
    "invoice_line": df_line, "payment": df_pay, "usage_summary": df_usage,
}
for name, df in DATASETS.items():
    d = f"{VOL_PATH}/{name}"
    os.makedirs(d, exist_ok=True)
    df.to_csv(f"{d}/{name}.csv", index=False)
    print(f"{name:24s} {len(df):6d} rows -> {d}/{name}.csv")
