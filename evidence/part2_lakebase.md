# Evidence — Part 2: Lakebase (agent context/memory layer)

Lakebase is the agent's context layer: short-term (conversation) + long-term (subscriber
facts, pgvector). Provisioned + smoke-tested from a single notebook (`10_lakebase_setup`),
parametrized by branch. Dev/prod = two copy-on-write branches of one project.

## Project — created (SDK `w.postgres`)

```
projects/acmetel   PG17   owner david.thomas@databricks.com
  autoscaling 1 CU min/max, suspend after 86400s (scale-to-zero)
```

## Branches — dev + prod, copy-on-write

```
production   state=READY  default=True   parent=-                  size=0
demo-dev     state=READY  default=False  parent=projects/acmetel   size=0   (48h TTL)
```

`demo-dev` forked from `production` with zero data copied (copy-on-write) — isolated dev memory.

## Memory tiers provisioned (both branches) — TERMINATED SUCCESS

`AsyncCheckpointSaver.setup()` + `AsyncDatabricksStore.setup()` created the memory tables in
schema `acmetel_memory`; a put/search/delete smoke test of a subscriber fact passed in-run.

Tables in `acmetel_memory` (verified via psycopg):
```
checkpoint_blobs   checkpoint_migrations   checkpoint_writes   checkpoints
store              store_migrations        store_vectors       vector_migrations
```
pgvector extension: `vector 0.8.0`

Short-term tier = `checkpoints*` (keyed by thread_id). Long-term tier = `store`/`store_vectors`
(subscriber-namespaced, gte-large-en 1024-dim semantic recall). This is what Part 3's agent
connects to — same project/branch/schema.

## Validation coverage

`99_validate` now checks all four layers in one report (HTML + text): UC structure, medallion
layer parity, metric views, and **Lakebase memory** (connects to the branch via psycopg, counts
memory tables in `acmetel_memory`, confirms pgvector). Takes a `lakebase_branch` param
(default `production`). Ran SUCCESS with the Lakebase section active.

_Last updated: 2026-08-31_
