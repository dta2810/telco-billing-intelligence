"""Session tools for the AcmeTel billing agent.

The only code tool is `get_customer_key`, which resolves an AcmeTel subscriber
(customer_id) from a phone number (msisdn_primary) or identification number
(tax_id) and stores it in the LangGraph session state as `customer_key`. All
billing analytics come from the Genie space and the Unity Catalog functions,
which are attached as MCP tools in agent.py.

Note: AcmeTel data lives in Unity Catalog (`acmetel_demo.gold`), NOT in Lakebase
Postgres. Lookups therefore go through the SQL Statement Execution API against a
warehouse — not the Lakebase connection pool used for agent memory.
"""

import json
import logging
import os
from typing import Annotated, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

logger = logging.getLogger(__name__)

_w = WorkspaceClient()

# AcmeTel Unity Catalog location + warehouse for deterministic subscriber lookup.
CATALOG = os.getenv("CATALOG", "dt_serverless_stable_isqgt5_catalog")
SCHEMA = os.getenv("SCHEMA", "acmetel_gold")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "2f3030c18eff5d1a")


def _make_command(customer_key: Optional[str], content: str, state: dict) -> Command:
    """Build a Command that updates customer_key and includes the required ToolMessage."""
    tool_call_id = ""
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "get_customer_key":
                    tool_call_id = tc.get("id", "")
                    break
            if tool_call_id:
                break

    return Command(
        update={
            "customer_key": customer_key,
            "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        },
    )


@tool
def get_customer_key(
    identifier: str,
    identifier_type: str,
    state: Annotated[dict, InjectedState],
) -> Command:
    """Identify an AcmeTel subscriber by phone number or identification number.

    Stores the resolved customer_id in the session so it can be reused across the
    conversation and used to scope this subscriber's long-term memory. Call this
    FIRST, before answering any billing question.

    Args:
        identifier: The subscriber's phone number (MSISDN) or identification/tax number.
        identifier_type: Either "phone_number" or "identification".
    """
    if identifier_type not in ("phone_number", "identification"):
        return _make_command(
            None,
            json.dumps({"error": "identifier_type must be 'phone_number' or 'identification'"}),
            state,
        )

    column = "msisdn_primary" if identifier_type == "phone_number" else "tax_id"
    statement = (
        f"SELECT customer_id, full_name, segment, status "
        f"FROM {CATALOG}.{SCHEMA}.customer WHERE {column} = :ident LIMIT 1"
    )

    try:
        resp = _w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=statement,
            parameters=[StatementParameterListItem(name="ident", value=identifier)],
            wait_timeout="30s",
        )
        rows = resp.result.data_array if (resp.result and resp.result.data_array) else None
        if rows:
            customer_id, full_name, segment, status = rows[0][0], rows[0][1], rows[0][2], rows[0][3]
            payload = {
                "customer_key": customer_id,
                "full_name": full_name,
                "segment": segment,
                "status": status,
            }
            return _make_command(customer_id, json.dumps(payload, ensure_ascii=False), state)
        return _make_command(
            None,
            json.dumps({"error": f"No subscriber found with {identifier_type}: {identifier}"}),
            state,
        )
    except Exception as e:
        logger.error(f"Error looking up subscriber: {e}")
        return _make_command(
            None,
            json.dumps({"error": f"Failed to look up subscriber: {str(e)}"}),
            state,
        )
