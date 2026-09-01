# AcmeTel Billing Intelligence — an end-to-end data journey

## The problem we solved

Telco billing support restarts every interaction from zero. The customer re-explains their
issue, the rep re-asks who they are, and nothing learned last time carries into the next call.
Without memory, personalization is impossible and retention is reactive — you cannot act on a
promise you made last week if the system never remembered making it.

**What we built:** a governed billing platform for a fictitious LATAM telco ("AcmeTel") plus an
AI assistant that answers from real data **and remembers each subscriber across calls, channels,
and languages** — on one Databricks platform, end to end.

## The value it creates

- **Lower handle time** — the assistant opens already aware of the account: overdue balance,
  expired discount, contract status, best next offer. No re-identification, no digging.
- **Proactive retention** — it recalls preferences, disputes, price sensitivity and promises, so
  the next contact continues the relationship instead of restarting it.
- **Governed, not a black box** — every remembered fact is a Postgres row under Unity Catalog:
  queryable, auditable, access-controlled. Business KPIs (ARPU, collection rate, revenue at risk)
  come from the same governed model.

Seeded into the data so the value is demonstrable: **234** subscribers whose discount expired
last month (their bill jumped), **40** delinquent accounts (revenue at risk), **174** lines with
data overage (mis-sized plans), and contracts inside the 60-day retention window.

## See it work

The journey is one integrated flow, not stitched-together demos. Every stage below ran on a
Databricks (FEVM) workspace and committed its output as **text** in [`evidence/`](evidence/) —
row counts, query results, generated SQL, and real agent answers (not screenshots).

| Stage | What it does | Evidence |
|-------|--------------|----------|
| **Lakeflow** | Synthetic raw billing data → Auto Loader → bronze → silver → gold, run as one serverless Job | [`evidence/part1_setup_generate.md`](evidence/part1_setup_generate.md), [`evidence/part1_job_run.md`](evidence/part1_job_run.md) |
| **Unity Catalog** | 10 governed gold tables with column comments (the context layer) + 8 metric views (ARPU, collection rate, revenue at risk, …) | [`evidence/part1_setup_generate.md`](evidence/part1_setup_generate.md) |
| **Lakebase** | The agent's context layer — short-term (conversation) + long-term (subscriber facts, pgvector), dev/prod copy-on-write branches | [`evidence/part2_lakebase.md`](evidence/part2_lakebase.md) |
| **ML / GenAI** | A LangGraph + Claude agent, embedded in the app, with 4 UC-function tools + Genie + memory | [`evidence/part3_uc_functions.md`](evidence/part3_uc_functions.md), [`evidence/part5_app.md`](evidence/part5_app.md) |
| **Genie Room** | Natural-language questions over the gold model → SQL → answer | [`evidence/part4_genie.md`](evidence/part4_genie.md) |
| **Databricks App** | Executive KPI dashboard + Customer-360 with the memory assistant, one deployed app | [`evidence/part5_app.md`](evidence/part5_app.md) |

**The payoff, verified end to end** (from [`evidence/part5_app.md`](evidence/part5_app.md)): a rep
asks "how much does this customer owe and why?" and the assistant answers with the balance, dunning
stage, and the expired discount that caused the increase — then, told the customer prefers WhatsApp
and is price-sensitive, it **recalls those facts in a brand-new session**. Short-term and long-term
memory, working, on governed infrastructure.

## How the data flows

```
 synthetic raw (CSV)
        │  Lakeflow Job (serverless, Auto Loader)
        ▼
 bronze ─▶ silver ─▶ gold  ──────────────┐   Unity Catalog (comments + 8 metric views)
                      │                   │
                      ├─▶ Genie Room ─────┤   natural-language SQL over gold
                      │                   │
                      └─▶ UC functions ───┤   discount / payment / NBO / plan-change
                                          │
 Lakebase (Postgres + pgvector) ◀─────────┤   agent memory: short-term + long-term
   short-term: conversation                │
   long-term: subscriber facts             ▼
                              LangGraph + Claude agent (embedded)
                                          │
                                          ▼
                               Databricks App (Executive + Customer-360)
```

The agent reaches Genie and the UC functions as **MCP tools**, reads/writes memory on **Lakebase**,
and runs **in-process inside the app** — one deployment, no service-to-service hop.

## Repository layout

```
fe_bar/
  README.md            # this file
  CONVENTIONS.md       # build standard (English, naming, medallion, evidence)
  databricks.yml       # DABs bundle for the medallion Lakeflow Job
  notebooks/           # every stage deploys from a notebook
    config             # naming — single source of truth
    00_setup_uc … 05_metric_views   # Phase 1: medallion
    10_lakebase_setup, 11_uc_functions, 12_genie, 13_agent   # Phase 2: intelligence
    14_app             # deploy the app (SDK w.apps)
    99_validate        # validates all six stages (HTML + text report)
  app/                 # FastAPI + React app with the embedded memory agent
  evidence/            # committed run output, readable as text
```

## Run it yourself

Everything deploys from notebooks against a Databricks workspace (serverless).

```bash
# 1. Medallion (data journey) — deploy + run the Lakeflow Job
databricks bundle deploy -t dev -p <profile>
databricks bundle run acmetel_medallion -t dev -p <profile>

# 2. Intelligence + app — run the notebooks in order (import + jobs submit, or the UI)
#    10_lakebase_setup → 11_uc_functions → 12_genie → 14_app

# 3. Validate all six stages
#    run 99_validate → HTML report + text summary
```

Naming is driven by `notebooks/config`; the workspace profile is the only environment-specific
value. **AcmeTel is fictitious** — no real customer, branding, or PII appears anywhere.

## Architecture notes

- **Medallion, one direction:** generate → landing (raw files) → bronze (Auto Loader, as-ingested)
  → silver (typed + deduped) → gold (business model) → metric views. Orchestrated as a single
  serverless Lakeflow Job.
- **Unity Catalog as the context layer:** table and column `COMMENT`s are read by Genie and the
  agent, so semantics live once in the catalog, not scattered in prompts.
- **Lakebase as the agent's memory:** short-term via a checkpoint saver (keyed by conversation),
  long-term via a subscriber-namespaced vector store (`gte-large-en`), on copy-on-write dev/prod
  branches of one project.
- **Agent embedded in the app:** a LangGraph agent (Claude) with `get_customer_key` + Genie + UC
  functions + memory tools, called in-process by the FastAPI backend — one governed app, not a
  fleet of services.
