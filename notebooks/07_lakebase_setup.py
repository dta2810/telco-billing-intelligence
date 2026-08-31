# Databricks notebook source
# MAGIC %pip install --quiet "databricks-sdk>=0.81.0" "databricks-langchain[memory]>=0.17.0" "psycopg[binary]>=3.0" nest_asyncio
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %run ./config

# COMMAND ----------
import asyncio
import nest_asyncio
import psycopg
nest_asyncio.apply()
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import Project, ProjectSpec, Branch, BranchSpec
from google.protobuf.duration_pb2 import Duration

dbutils.widgets.text("branch", "production")
BRANCH = dbutils.widgets.get("branch")
DEV_TTL_SECONDS = 172800  # dev branch auto-delete (48h); production is permanent

w = WorkspaceClient()

# COMMAND ----------
# create project (idempotent) — auto-creates production branch + primary endpoint
proj_path = f"projects/{LAKEBASE_PROJECT}"
try:
    project = w.postgres.get_project(name=proj_path)
    print(f"project exists: {proj_path}")
except Exception:
    project = w.postgres.create_project(
        project=Project(spec=ProjectSpec(display_name="AcmeTel agent memory")),
        project_id=LAKEBASE_PROJECT,
    ).wait()
    print(f"project created: {proj_path}")

# COMMAND ----------
# ensure target branch (production auto-exists; create dev copy-on-write if missing)
branch_path = f"{proj_path}/branches/{BRANCH}"
try:
    branch = w.postgres.get_branch(name=branch_path)
    print(f"branch exists: {BRANCH}")
except Exception:
    branch = w.postgres.create_branch(
        parent=proj_path,
        branch=Branch(spec=BranchSpec(source_branch=f"{proj_path}/branches/production",
                                      ttl=Duration(seconds=DEV_TTL_SECONDS))),
        branch_id=BRANCH,
    ).wait()
    print(f"branch created: {BRANCH}")
st = branch.status
print(f"  state={st.current_state} source_lsn={st.source_branch_lsn} parent={st.source_branch}")

# COMMAND ----------
# connect to the branch endpoint via OAuth credential
endpoint = list(w.postgres.list_endpoints(parent=branch_path))[0]
host = endpoint.status.hosts.host
cred = w.postgres.generate_database_credential(endpoint=endpoint.name)
user = w.current_user.me().user_name

conn = psycopg.connect(host=host, dbname="databricks_postgres", user=user,
                       password=cred.token, sslmode="require", autocommit=True)
print(f"connected: host={host} db=databricks_postgres user={user}")

# COMMAND ----------
# provision memory schema + pgvector
with conn.cursor() as cur:
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {LAKEBASE_MEMORY_SCHEMA}")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("SELECT extname FROM pg_extension WHERE extname='vector'")
    print("pgvector:", cur.fetchone())

# COMMAND ----------
# provision + smoke-test the two memory tiers (creates checkpoints*/store* tables)
from databricks_langchain import AsyncCheckpointSaver, AsyncDatabricksStore

kwargs = {"project": LAKEBASE_PROJECT, "branch": BRANCH, "schema": LAKEBASE_MEMORY_SCHEMA}

async def provision_and_test():
    async with AsyncCheckpointSaver(**kwargs) as ckpt, \
               AsyncDatabricksStore(embedding_endpoint=EMBEDDING_ENDPOINT,
                                    embedding_dims=EMBEDDING_DIMS, **kwargs) as store:
        await ckpt.setup()
        await store.setup()
        ns = ("subscriber_memories", "CUS-000001")
        await store.aput(ns, "smoke_test", {"note": "context layer live"})
        hits = await store.asearch(ns, query="context layer", limit=1)
        await store.adelete(ns, "smoke_test")
        return [(i.key, i.value) for i in hits]

result = asyncio.run(provision_and_test())
print("short-term tier: AsyncCheckpointSaver.setup() OK (checkpoints* tables)")
print("long-term tier:  AsyncDatabricksStore.setup() OK (store/store_vectors, pgvector)")
print("smoke put/search/delete:", result)

# COMMAND ----------
# evidence: memory tables in the schema
with conn.cursor() as cur:
    cur.execute(f"""SELECT tablename FROM pg_tables
                    WHERE schemaname='{LAKEBASE_MEMORY_SCHEMA}' ORDER BY tablename""")
    tables = [r[0] for r in cur.fetchall()]
print(f"project={LAKEBASE_PROJECT} branch={BRANCH} schema={LAKEBASE_MEMORY_SCHEMA}")
print("memory tables:", tables)
conn.close()
