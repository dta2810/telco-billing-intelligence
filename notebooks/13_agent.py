# Databricks notebook source
# MAGIC %pip install --quiet "databricks-sdk>=0.81.0" "databricks-langchain[memory]>=0.17.0" "databricks-agents>=1.9.3" "langgraph>=1.1.9" "langchain-mcp-adapters>=0.2.1" mlflow nest_asyncio
# MAGIC %restart_python

# COMMAND ----------
# MAGIC %run ./config

# COMMAND ----------
import os
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

# resolve runtime values to bake into the model code
GENIE_SPACE_ID = next(s.space_id for s in w.genie.list_spaces().spaces if s.title == GENIE_SPACE_TITLE)
WAREHOUSE_ID = WAREHOUSE_ID or sorted((x for x in w.warehouses.list() if x.warehouse_type and x.warehouse_type.value == "PRO"),
                      key=lambda x: (not x.enable_serverless_compute, x.state.value != "RUNNING"))[0].id
LAKEBASE_BRANCH = "production"
print("genie:", GENIE_SPACE_ID, "| warehouse:", WAREHOUSE_ID)

# COMMAND ----------
# write the agent code (Models-from-Code) with config baked in
AGENT_SRC = '''
import asyncio, json
from datetime import date
from typing import Annotated, Any, Optional, Sequence, TypedDict
import mlflow, nest_asyncio
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem
from databricks_langchain import (ChatDatabricks, DatabricksMCPServer,
    DatabricksMultiServerMCPClient, AsyncCheckpointSaver, AsyncDatabricksStore)
from langchain.agents import create_agent
from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.prebuilt import InjectedState
from langgraph.store.base import BaseStore
from langgraph.types import Command
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (ResponsesAgentRequest, ResponsesAgentResponse,
    to_chat_completions_input)
nest_asyncio.apply()

CATALOG = "__CATALOG__"; GOLD = "__GOLD__"
GENIE_SPACE_ID = "__GENIE__"; LLM_ENDPOINT = "__LLM__"; WAREHOUSE_ID = "__WH__"
LB_PROJECT = "__LBP__"; LB_BRANCH = "__LBB__"; LB_SCHEMA = "__LBS__"
EMB = "__EMB__"; EMB_DIMS = __EMBD__
NAMESPACE_PREFIX = "subscriber_memories"
SYSTEM_PROMPT = ("You are the billing assistant for AcmeTel, a LATAM telecom operator. "
    "Identify the subscriber first with get_customer_key (unless a customer_id is already given), "
    "then answer billing questions from the Genie space and UC functions, and remember durable "
    "subscriber facts with the memory tools. Be concise, don't restate the question, answer in the "
    "user's language.")

_w = WorkspaceClient()

@tool
def get_customer_key(identifier: str, identifier_type: str,
                     state: Annotated[dict, InjectedState]) -> Command:
    """Identify an AcmeTel subscriber by phone number or identification number. Call FIRST.
    Args: identifier: phone (MSISDN) or tax id. identifier_type: "phone_number" or "identification"."""
    col = "msisdn_primary" if identifier_type == "phone_number" else "tax_id"
    tcid = ""
    for m in reversed(state.get("messages", [])):
        if getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                if tc.get("name") == "get_customer_key": tcid = tc.get("id", "")
    try:
        r = _w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=f"SELECT customer_id, full_name, segment, status FROM {CATALOG}.{GOLD}.customer WHERE {col} = :ident LIMIT 1",
            parameters=[StatementParameterListItem(name="ident", value=identifier)], wait_timeout="30s")
        rows = r.result.data_array if (r.result and r.result.data_array) else None
        if rows:
            cid = rows[0][0]
            payload = {"customer_key": cid, "full_name": rows[0][1], "segment": rows[0][2], "status": rows[0][3]}
            return Command(update={"customer_key": cid,
                "messages": [ToolMessage(content=json.dumps(payload, ensure_ascii=False), tool_call_id=tcid)]})
        return Command(update={"messages": [ToolMessage(content=json.dumps({"error": "not found"}), tool_call_id=tcid)]})
    except Exception as e:
        return Command(update={"messages": [ToolMessage(content=json.dumps({"error": str(e)}), tool_call_id=tcid)]})

def _subject(state, config):
    if isinstance(state, dict) and state.get("customer_key"): return str(state["customer_key"])
    uid = config.get("configurable", {}).get("user_id")
    return str(uid) if uid else None
def _ns(subj): return (NAMESPACE_PREFIX, subj.replace(".", "-"))

def memory_tools():
    @tool
    async def list_user_memories(config: RunnableConfig, state: Annotated[dict, InjectedState]) -> str:
        """List ALL stored facts about the current subscriber (full profile)."""
        subj = _subject(state, config); store = config.get("configurable", {}).get("store")
        if not subj or not store: return "No subscriber identified yet."
        res = await store.asearch(_ns(subj), limit=100)
        return "Profile:\\n" + "\\n".join(f"- [{i.key}]: {json.dumps(i.value, ensure_ascii=False)}" for i in res) if res else "No memories."
    @tool
    async def get_user_memory(query: str, config: RunnableConfig, state: Annotated[dict, InjectedState]) -> str:
        """Semantic recall of subscriber facts matching the query."""
        subj = _subject(state, config); store = config.get("configurable", {}).get("store")
        if not subj or not store: return "No subscriber identified yet."
        res = await store.asearch(_ns(subj), query=query, limit=5)
        return "\\n".join(f"- [{i.key}]: {json.dumps(i.value, ensure_ascii=False)}" for i in res) if res else "No memories."
    @tool
    async def save_user_memory(memory_key: str, memory_data_json: str, config: RunnableConfig,
                               state: Annotated[dict, InjectedState]) -> str:
        """Save a durable subscriber fact as a JSON object, e.g. {"preferred_channel":"whatsapp"}."""
        subj = _subject(state, config); store = config.get("configurable", {}).get("store")
        if not subj or not store: return "No subscriber identified yet."
        await store.aput(_ns(subj), memory_key, json.loads(memory_data_json))
        return f"Saved '{memory_key}'."
    return [list_user_memories, get_user_memory, save_user_memory]

class StatefulState(TypedDict, total=False):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    customer_key: Optional[str]

def _host():
    return _w.config.host

class AcmeTelAgent(ResponsesAgent):
    def _lb(self): return {"project": LB_PROJECT, "branch": LB_BRANCH, "schema": LB_SCHEMA}
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        ci = dict(request.custom_inputs or {})
        thread_id = ci.get("thread_id") or "conv-default"
        seeded = ci.get("customer_id") or ci.get("customer_key")
        msgs = to_chat_completions_input([i.model_dump() for i in request.input])
        async def _run():
            mcp = DatabricksMultiServerMCPClient([
                DatabricksMCPServer(name="genie", url=f"{_host()}/api/2.0/mcp/genie/{GENIE_SPACE_ID}", workspace_client=_w),
                DatabricksMCPServer(name="ucfns", url=f"{_host()}/api/2.0/mcp/functions/{CATALOG}/{GOLD}", workspace_client=_w),
            ])
            tools = [get_customer_key]
            try: tools.extend(await mcp.get_tools())
            except Exception: pass
            tools.extend(memory_tools())
            async with AsyncCheckpointSaver(**self._lb()) as ckpt, \\
                       AsyncDatabricksStore(embedding_endpoint=EMB, embedding_dims=EMB_DIMS, **self._lb()) as store:
                await ckpt.setup(); await store.setup()
                prompt = f"Today is {date.today().isoformat()}.\\n" + SYSTEM_PROMPT
                if seeded:
                    prompt += f"\\nThe subscriber is already identified as customer_id={seeded}; skip get_customer_key, call list_user_memories, and pass this customer_id to the tools."
                agent = create_agent(model=ChatDatabricks(endpoint=LLM_ENDPOINT), tools=tools,
                    system_prompt=prompt, checkpointer=ckpt, store=store, state_schema=StatefulState)
                state = {"messages": msgs}
                if seeded: state["customer_key"] = str(seeded)
                cfg = {"configurable": {"thread_id": thread_id, "store": store, "user_id": seeded}}
                out = await agent.ainvoke(state, cfg)
                return out["messages"][-1].content
        text = asyncio.run(_run())
        if isinstance(text, list):
            text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=text, id="msg_1")],
            custom_outputs={"thread_id": thread_id})

mlflow.langchain.autolog()
mlflow.models.set_model(AcmeTelAgent())
'''
repl = {"__CATALOG__": CATALOG, "__GOLD__": GOLD, "__GENIE__": GENIE_SPACE_ID, "__LLM__": LLM_ENDPOINT,
        "__WH__": WAREHOUSE_ID, "__LBP__": LAKEBASE_PROJECT, "__LBB__": LAKEBASE_BRANCH,
        "__LBS__": LAKEBASE_MEMORY_SCHEMA, "__EMB__": EMBEDDING_ENDPOINT, "__EMBD__": str(EMBEDDING_DIMS)}
for k, v in repl.items():
    AGENT_SRC = AGENT_SRC.replace(k, v)
with open("agent.py", "w") as f:
    f.write(AGENT_SRC)
print("agent.py written")

# COMMAND ----------
# log + register with passthrough-auth resources
import mlflow
from mlflow.models.resources import (DatabricksServingEndpoint, DatabricksFunction,
    DatabricksGenieSpace, DatabricksLakebase)
from mlflow.tracking import MlflowClient

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment(f"/Users/{w.current_user.me().user_name}/acmetel_agent")
FULL_NAME = f"{CATALOG}.{GOLD}.{AGENT_MODEL_NAME}"
UC_FNS = ["check_discount_status", "get_payment_status", "get_next_best_offer", "simulate_plan_change"]

resources = [
    DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT),
    DatabricksServingEndpoint(endpoint_name=EMBEDDING_ENDPOINT),
    DatabricksGenieSpace(genie_space_id=GENIE_SPACE_ID),
    DatabricksLakebase(database_instance_name=LAKEBASE_PROJECT),
    *[DatabricksFunction(function_name=f"{CATALOG}.{GOLD}.{fn}") for fn in UC_FNS],
]

with mlflow.start_run():
    info = mlflow.pyfunc.log_model(
        name="agent", python_model="agent.py", resources=resources,
        input_example={"input": [{"role": "user", "content": "How much does customer CUS-000002 owe?"}],
                       "custom_inputs": {"customer_id": "CUS-000002"}},
        pip_requirements=["mlflow", "databricks-langchain[memory]", "databricks-agents",
                          "langgraph", "langchain-mcp-adapters", "psycopg[binary]", "nest_asyncio", "pydantic>=2"],
        registered_model_name=FULL_NAME)
print("logged:", info.model_uri, "version", info.registered_model_version)

# COMMAND ----------
# pre-deploy smoke: run the agent in-process (fail fast before the ~15 min deploy)
val = mlflow.models.predict(
    model_uri=info.model_uri, env_manager="local",
    input_data={"input": [{"role": "user", "content": "How much does customer CUS-000002 owe?"}],
                "custom_inputs": {"customer_id": "CUS-000002"}})
print("smoke output:", str(val)[:400])

# COMMAND ----------
# promote @prod
client = MlflowClient(registry_uri="databricks-uc")
client.set_registered_model_alias(FULL_NAME, "prod", info.registered_model_version)
print("aliased @prod ->", info.registered_model_version)

# COMMAND ----------
# deploy (agent serving endpoints scale to zero by default)
from databricks import agents
dep = agents.deploy(FULL_NAME, info.registered_model_version,
                    endpoint_name=AGENT_ENDPOINT, tags={"project": "fe_bar"})
print("endpoint:", dep.endpoint_name)
print("query:", dep.query_endpoint)
