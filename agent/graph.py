"""
LangGraph workflow definition.
Wires together the individual processing nodes into a
stateful, checkpointed graph that powers the logistics assistant.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    router_node,
    chat_node,
    sql_generator_node,
    sql_executor_node,
    sql_corrector_node,
    responder_node,
)


# ── Routing predicates ───────────────────────────────────────────

def _decide_after_router(state: AgentState) -> str:
    """After intent classification, pick the SQL or chat branch."""
    if state.get("intent") == "sql":
        return "generator"
    return "chat"


def _decide_after_executor(state: AgentState) -> str:
    """After running SQL, either retry with corrector or move to response."""
    has_error = state.get("error") is not None
    retries_left = state.get("revision_count", 0) < 3

    if has_error and retries_left:
        return "corrector"
    return "responder"


# ── Graph assembly ───────────────────────────────────────────────

_graph_builder = StateGraph(AgentState)

# Register every processing node
_graph_builder.add_node('router', router_node)
_graph_builder.add_node('chat', chat_node)
_graph_builder.add_node('generator', sql_generator_node)
_graph_builder.add_node('executor', sql_executor_node)
_graph_builder.add_node('corrector', sql_corrector_node)
_graph_builder.add_node('responder', responder_node)

# The pipeline always starts at the router
_graph_builder.set_entry_point('router')

# Conditional branch after routing
_graph_builder.add_conditional_edges(
    'router',
    _decide_after_router,
    {'generator': 'generator', 'chat': 'chat'},
)

# Fixed transitions
_graph_builder.add_edge('chat', 'responder')
_graph_builder.add_edge('generator', 'executor')

# Conditional branch after SQL execution
_graph_builder.add_conditional_edges(
    'executor',
    _decide_after_executor,
    {'corrector': 'corrector', 'responder': 'responder'},
)

# Correction feeds back into the executor for another attempt
_graph_builder.add_edge('corrector', 'executor')

# The responder is always the terminal node
_graph_builder.add_edge('responder', END)

# Compile with in-memory checkpointing
_checkpoint_store = MemorySaver()
app = _graph_builder.compile(checkpointer=_checkpoint_store)
