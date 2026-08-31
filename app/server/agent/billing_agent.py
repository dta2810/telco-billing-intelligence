"""Embedded billing agent — runs in-process in the FastAPI app (no HTTP hop).

Short-term (conversation) + long-term (subscriber) memory on Lakebase, Genie space and
UC functions as MCP tools, Claude as the LLM. Exposes one async entrypoint, answer().
"""
import os
from datetime import date
from typing import Annotated, Any, Optional, Sequence, TypedDict

from databricks.sdk import WorkspaceClient
from databricks_langchain import (ChatDatabricks, DatabricksMCPServer,
    DatabricksMultiServerMCPClient, AsyncCheckpointSaver, AsyncDatabricksStore)
from langchain.agents import create_agent
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from server.agent.tools import get_customer_key
from server.agent.memory_tools import memory_tools

CATALOG = os.environ.get("CATALOG", "dt_serverless_stable_isqgt5_catalog")
SCHEMA = os.environ.get("SCHEMA", "acmetel_gold")
GENIE_SPACE_ID = os.environ["GENIE_SPACE_ID"]
LLM_ENDPOINT = os.environ.get("LLM_ENDPOINT", "databricks-claude-sonnet-4-5")
EMBEDDING_ENDPOINT = os.environ.get("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
EMBEDDING_DIMS = int(os.environ.get("EMBEDDING_DIMS", "1024"))
LAKEBASE = {
    "project": os.environ["LAKEBASE_PROJECT"],
    "branch": os.environ.get("LAKEBASE_BRANCH", "production"),
    "schema": os.environ.get("LAKEBASE_SCHEMA", "acmetel_memory"),
}

SYSTEM_PROMPT = """LANGUAGE RULE (highest priority): detect the language of the user's LAST message \
and write your ENTIRE reply in that same language. Mirror the user turn by turn.

You assist AcmeTel (a LATAM telecom operator) call-center reps resolving billing inquiries: \
expired discounts, past-due balances, contracts, charges, plan upgrades. Be concise and \
empathetic: at most 4 sentences.

FLOW:
1. Identify the subscriber first: ask for a phone or identification number and use get_customer_key \
   to resolve their customer_id. Do not answer billing questions before identifying the subscriber.
2. Memory recall — pick the tool by intent: at session start or open questions ("what do we know \
   about them?") use list_user_memories (full profile); for a targeted lookup use get_user_memory \
   (semantic). Personalize with what you recall.
3. For analytical/open questions ("why did my bill go up?", charge detail, usage, metrics) use the \
   Genie tool over the AcmeTel billing space.
4. For exact actions/calculations use the Unity Catalog functions, passing the customer_id:
   check_discount_status, get_payment_status, get_next_best_offer, simulate_plan_change.
5. LONG-TERM MEMORY: persist durable subscriber facts with save_user_memory (one memory_key per \
   field, language-neutral JSON). Canonical keys: preferred_channel, preferred_language, \
   open_disputes[list], price_sensitivity, churn_risk, promises_made[list], plan_interest, \
   sentiment_notes. Be PROACTIVE — save durable facts as they surface. Lists: save_user_memory \
   OVERWRITES per key, so read the current value first and re-save the full list with the new item. \
   HARD RULE: never claim you saved something without actually calling save_user_memory in the same \
   turn. Use delete_user_memory if asked to forget.

If a customer or invoice does not exist, say so clearly.
"""


class State(TypedDict, total=False):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    customer_key: Optional[str]


def _host():
    return WorkspaceClient().config.host


async def answer(message: str, thread_id: str, customer_id: Optional[str] = None,
                 customer_context: Optional[str] = None) -> str:
    w = WorkspaceClient()
    mcp = DatabricksMultiServerMCPClient([
        DatabricksMCPServer(name="genie", url=f"{_host()}/api/2.0/mcp/genie/{GENIE_SPACE_ID}", workspace_client=w),
        DatabricksMCPServer(name="ucfns", url=f"{_host()}/api/2.0/mcp/functions/{CATALOG}/{SCHEMA}", workspace_client=w),
    ])
    tools = [get_customer_key]
    try:
        tools.extend(await mcp.get_tools())
    except Exception:
        pass
    tools.extend(memory_tools())

    prompt = f"Today is {date.today().isoformat()}.\n" + SYSTEM_PROMPT
    if customer_id:
        prompt += (f"\nThe subscriber is already identified as customer_id={customer_id}; skip "
                   f"get_customer_key, call list_user_memories, and pass this customer_id to the tools.")
    if customer_context:
        prompt += f"\nCURRENT ACCOUNT STATUS (live, precomputed): {customer_context}"

    async with AsyncCheckpointSaver(**LAKEBASE) as ckpt, \
               AsyncDatabricksStore(embedding_endpoint=EMBEDDING_ENDPOINT,
                                    embedding_dims=EMBEDDING_DIMS, **LAKEBASE) as store:
        await ckpt.setup()
        await store.setup()
        agent = create_agent(model=ChatDatabricks(endpoint=LLM_ENDPOINT), tools=tools,
                             system_prompt=prompt, checkpointer=ckpt, store=store, state_schema=State)
        state: dict[str, Any] = {"messages": [{"role": "user", "content": message}]}
        if customer_id:
            state["customer_key"] = str(customer_id)
        cfg = {"configurable": {"thread_id": thread_id, "store": store, "user_id": customer_id}}
        out = await agent.ainvoke(state, cfg)
        content = out["messages"][-1].content
        if isinstance(content, list):
            content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
        return content
