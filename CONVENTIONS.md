# AcmeTel Solution — Build Standard

The engineering standard for this end-to-end solution. Every notebook, script, and asset in
this repository follows it. The repository is self-contained, packageable, and shareable.

---

## 1. What this is

An integrated, end-to-end data journey for a fictitious LATAM telco ("AcmeTel"): raw billing
data flows through a governed medallion, is served operationally, made intelligent with an
agent, made queryable in natural language, and surfaced in a business app. The build proves
each stage ran, in text.

**AcmeTel is fictitious.** No real customer name, branding, or data appears anywhere. The
repository is safe to share externally.

---

## 2. Repository layout

```
fe_bar/
  CONVENTIONS.md      # this standard
  README.md           # client-facing entry — leads with the business outcome
  databricks.yml      # DABs bundle: the Lakeflow Job (serverless)
  notebooks/          # medallion notebooks, run in order by the Job
    config            # naming conventions — single source of truth
    00_setup_uc       # catalog + schemas + volume + gold table contracts
    01_generate_raw   # synthetic raw data → landing volume
    02_bronze         # Auto Loader: raw → bronze
    03_silver         # typed + quality → silver
    04_gold           # business model → gold
    05_metric_views   # semantic metric views
  evidence/           # committed run output, readable as text
```

---

## 3. Naming conventions

All names come from `notebooks/config`, consumed by every notebook via `%run ./config`.
Never hardcode a catalog, schema, volume, or table name in a notebook — reference `config`.

| Constant | Value |
|---|---|
| `CATALOG` | `dt_serverless_stable_isqgt5_catalog` (workspace catalog — no metastore CREATE CATALOG on FEVM) |
| Schemas | `acmetel_landing`, `acmetel_bronze`, `acmetel_silver`, `acmetel_gold` |
| `VOLUME` | `raw` (under the landing schema) |
| `t(schema, name)` | fully-qualified name helper |

Schema names are prefixed `acmetel_` to stay grouped in the shared workspace catalog. Downstream
assets (agent, Genie, UC functions) resolve gold as `CATALOG.acmetel_gold.<table>` — keep it stable.

---

## 4. Medallion architecture

One direction of flow, no shortcuts:

```
generate → landing (raw files) → bronze (as-ingested) → silver (typed + clean) → gold (business) → metric views
```

- **Landing** — raw CSV files per entity in the `raw` volume.
- **Bronze** — Auto Loader (`cloudFiles`, `availableNow`), all columns as string, plus
  `_ingested_at` and `_source_file`.
- **Silver** — cast to the gold contract types, dedup on primary key, drop rows with null keys.
- **Gold** — the business model. Table and column `COMMENT`s are the governed context layer.
- **Metric views** — reusable KPIs/KRIs as the semantic layer.

Orchestration is a single **Lakeflow Job** (multi-task, serverless) defined in `databricks.yml`.
Notebooks are the unit of work; the Job is the pipeline.

---

## 5. Language

Everything is in **English** — code, identifiers, comments, SQL `COMMENT` clauses, seed data
values (plan names, promotion names, line-item descriptions, tax labels), and documentation.

---

## 6. Code style

- Comments are short, step-level labels only (e.g. `# raw → bronze`).
- No explanatory docstrings or inline rationale. Rationale lives in this file and the README.
- SQL `COMMENT` clauses are **not** code comments — they are the functional UC context layer
  that Genie reads. Keep them descriptive and in English.

---

## 7. Execution evidence

Source code alone does not prove the build ran. Every stage commits its output as **text** in
`evidence/` — row counts per layer, query results, model/agent output, generated SQL. Never a
screenshot in place of the output itself.

---

## 8. Deployment

- Target is a FEVM (FE Vending Machine) workspace, serverless compute.
- Deploy and run with the DABs bundle:
  ```
  databricks bundle deploy -t dev -p <fevm-profile>
  databricks bundle run acmetel_medallion -t dev -p <fevm-profile>
  ```
- The workspace profile is the only environment-specific value; naming is portable.

---

_Last updated: 2026-08-28_
