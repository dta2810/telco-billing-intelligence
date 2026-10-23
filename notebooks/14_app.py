# Databricks notebook source
# MAGIC %pip install --quiet "databricks-sdk>=0.81.0"
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %run ./config

# COMMAND ----------
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import App, AppDeployment
w = WorkspaceClient()

APP_NAME = "acmetel-billing-360"
SRC = f"/Workspace/Users/{w.current_user.me().user_name}/fe_bar_app_src"  # app source synced here (incl. frontend/dist)

# COMMAND ----------
# create the app (idempotent)
try:
    app = w.apps.get(name=APP_NAME)
    print("app exists:", app.name)
except Exception:
    app = w.apps.create(app=App(name=APP_NAME,
        description="AcmeTel Billing 360 — exec KPIs + customer-360 + embedded memory agent")).result()
    print("app created:", app.name)
sp_id = app.service_principal_client_id
print("app SP client_id:", sp_id)

# COMMAND ----------
# grant the app SP least-privilege access: catalog/schema USE + SELECT per table + EXECUTE per function
# (table/function-scoped, not schema-wide) ; Genie CAN_RUN ; Lakebase role handled separately
G = f"{CATALOG}.{GOLD}"
UC_FNS = ["check_discount_status", "get_payment_status", "get_next_best_offer", "simulate_plan_change"]
grants = [f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{sp_id}`",
          f"GRANT USE SCHEMA ON SCHEMA {G} TO `{sp_id}`"]
grants += [f"GRANT SELECT ON TABLE {G}.{t} TO `{sp_id}`" for t in ENTITIES]
grants += [f"GRANT SELECT ON VIEW {G}.{v} TO `{sp_id}`" for v in METRIC_VIEWS]
grants += [f"GRANT EXECUTE ON FUNCTION {G}.{f} TO `{sp_id}`" for f in UC_FNS]
for stmt in grants:
    spark.sql(stmt)
print(f"UC grants applied to app SP ({len(grants)} scoped grants)")

# Genie space CAN_RUN for the app SP
GENIE_SPACE_ID = next(s.space_id for s in w.genie.list_spaces().spaces if s.title == GENIE_SPACE_TITLE)
w.api_client.do("PATCH", f"/api/2.0/permissions/genie/{GENIE_SPACE_ID}",
    body={"access_control_list": [{"service_principal_name": sp_id, "permission_level": "CAN_RUN"}]})
print("Genie CAN_RUN granted; space:", GENIE_SPACE_ID)

# COMMAND ----------
# deploy from the synced workspace source (frontend must be built into app/frontend/dist first)
dep = w.apps.deploy(app_name=APP_NAME,
                    app_deployment=AppDeployment(source_code_path=SRC)).result()
print("deployment:", dep.deployment_id, dep.status.state if dep.status else "")
print("app url:", w.apps.get(name=APP_NAME).url)
