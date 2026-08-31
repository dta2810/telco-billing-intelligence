"""Long-term memory tools for the AcmeTel billing agent.

Memory is scoped to the SUBSCRIBER, not the call-center user: the namespace key is
the `customer_key` (AcmeTel customer_id) stored in session state by get_customer_key.
This is what lets the agent recall a subscriber's preferences/history across separate
support sessions (different threads, same subscriber).

Facts are stored as language-neutral JSON (e.g. {"preferred_channel": "whatsapp"}) so
recall works whether the conversation is in Spanish or English. Embeddings use
gte-large-en, so cross-language semantic recall is good but EN-centric.

Backed by AsyncDatabricksStore (Lakebase + pgvector). The store is passed in via
RunnableConfig.configurable.store from the streaming handler.
"""

import json
import logging
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)

NAMESPACE_PREFIX = "subscriber_memories"


def _resolve_subject(state: Optional[dict], config: RunnableConfig) -> Optional[str]:
    """The memory subject: the identified subscriber (customer_key) if present,
    otherwise the fallback user_id passed through config."""
    if isinstance(state, dict) and state.get("customer_key"):
        return str(state["customer_key"])
    user_id = config.get("configurable", {}).get("user_id")
    return str(user_id) if user_id else None


def _namespace(subject: str) -> tuple:
    return (NAMESPACE_PREFIX, subject.replace(".", "-"))


def memory_tools():
    """Factory returning the get/save/delete long-term memory tools."""

    @tool
    async def get_user_memory(
        query: str, config: RunnableConfig, state: Annotated[dict, InjectedState]
    ) -> str:
        """Recall saved facts about the current subscriber (preferences, past issues,
        prior decisions). Use this early to personalize the conversation.

        Args:
            query: What to look for in the subscriber's memories.
        """
        subject = _resolve_subject(state, config)
        if not subject:
            return "Memory not available - no subscriber identified yet (call get_customer_key first)."
        store: Optional[BaseStore] = config.get("configurable", {}).get("store")
        if not store:
            return "Memory not available - store not configured."

        results = await store.asearch(_namespace(subject), query=query, limit=5)
        if not results:
            return "No memories found for this subscriber."
        items = [f"- [{item.key}]: {json.dumps(item.value, ensure_ascii=False)}" for item in results]
        return f"Found {len(results)} relevant memories for this subscriber:\n" + "\n".join(items)

    @tool
    async def list_user_memories(
        config: RunnableConfig, state: Annotated[dict, InjectedState]
    ) -> str:
        """List ALL stored facts about the current subscriber — the full profile, with no
        semantic ranking. Use this for open questions like "what do we know about this
        customer?" or at the start of a session, so nothing is missed. For a specific lookup
        (e.g. "does he prefer email?"), use get_user_memory instead.
        """
        subject = _resolve_subject(state, config)
        if not subject:
            return "Memory not available - no subscriber identified yet (call get_customer_key first)."
        store: Optional[BaseStore] = config.get("configurable", {}).get("store")
        if not store:
            return "Memory not available - store not configured."

        # query=None → deterministic listing of every fact in the namespace (no vector ranking).
        results = await store.asearch(_namespace(subject), limit=100)
        if not results:
            return "No memories found for this subscriber."
        items = [f"- [{item.key}]: {json.dumps(item.value, ensure_ascii=False)}" for item in results]
        return f"Full profile — {len(results)} stored fact(s) for this subscriber:\n" + "\n".join(items)

    @tool
    async def save_user_memory(
        memory_key: str,
        memory_data_json: str,
        config: RunnableConfig,
        state: Annotated[dict, InjectedState],
    ) -> str:
        """Save a durable fact about the current subscriber so it persists across sessions.

        Store LANGUAGE-NEUTRAL facts as a JSON object (e.g. '{"preferred_channel": "whatsapp"}',
        '{"disputed_charge": "device_subsidy"}', '{"price_sensitive": true}').

        Args:
            memory_key: Short descriptive key (e.g., "preferred_channel", "disputed_charge").
            memory_data_json: JSON object with the fact to remember.
        """
        subject = _resolve_subject(state, config)
        if not subject:
            return "Cannot save memory - no subscriber identified yet (call get_customer_key first)."
        store: Optional[BaseStore] = config.get("configurable", {}).get("store")
        if not store:
            return "Cannot save memory - store not configured."

        try:
            memory_data = json.loads(memory_data_json)
            if not isinstance(memory_data, dict):
                return f"Failed: memory_data must be a JSON object, not {type(memory_data).__name__}"
            await store.aput(_namespace(subject), memory_key, memory_data)
            return f"Successfully saved memory '{memory_key}' for this subscriber."
        except json.JSONDecodeError as e:
            return f"Failed to save memory: Invalid JSON - {e}"

    @tool
    async def delete_user_memory(
        memory_key: str, config: RunnableConfig, state: Annotated[dict, InjectedState]
    ) -> str:
        """Delete a specific stored fact for the current subscriber (right-to-be-forgotten).

        Args:
            memory_key: The key of the memory to delete.
        """
        subject = _resolve_subject(state, config)
        if not subject:
            return "Cannot delete memory - no subscriber identified yet."
        store: Optional[BaseStore] = config.get("configurable", {}).get("store")
        if not store:
            return "Cannot delete memory - store not configured."
        await store.adelete(_namespace(subject), memory_key)
        return f"Successfully deleted memory '{memory_key}' for this subscriber."

    return [list_user_memories, get_user_memory, save_user_memory, delete_user_memory]
