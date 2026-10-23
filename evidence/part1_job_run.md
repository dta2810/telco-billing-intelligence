# Evidence — Part 1: end-to-end Lakeflow Job run

> Original build run (2026-08-31). Current numbers for the demo: [`run_2026-10-23.md`](run_2026-10-23.md) (data is synthetic and date-relative, so figures move each regeneration).

The medallion runs as a single serverless Lakeflow Job (DABs bundle `acmetel-medallion`),
not ad-hoc notebook submissions. Job chains 7 tasks with `depends_on`.

- Job id: `580232130642779` (`acmetel_medallion`)
- Deploy: `databricks bundle deploy --target dev`
- Run: `databricks bundle run acmetel_medallion --target dev`

## Run result — TERMINATED SUCCESS

```
OVERALL: TERMINATED SUCCESS
  setup_uc       TERMINATED SUCCESS
  generate_raw   TERMINATED SUCCESS
  bronze         TERMINATED SUCCESS
  silver         TERMINATED SUCCESS
  gold           TERMINATED SUCCESS
  metric_views   TERMINATED SUCCESS
  validate       TERMINATED SUCCESS
```

Task DAG: setup_uc → generate_raw → bronze → silver → gold → metric_views → validate.
The `validate` task is the final gate (structure + landing counts + seeded scenarios +
medallion layer parity + metric views); its HTML report renders in the notebook.

_Last updated: 2026-08-31_
