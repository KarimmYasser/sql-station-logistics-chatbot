"""
Shared state schema for the LangGraph pipeline.
Every node reads from and writes to this typed dictionary.
"""

from typing import TypedDict, Annotated, List, Union, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """
    Central data-bag flowing through the graph.

    Fields
    ------
    messages : accumulated LLM message history
    question : the raw user utterance
    sql_query : generated / corrected SQL string
    sql_result : rows returned by the database, or an error description
    error : latest execution error (None when no error)
    revision_count : how many correction cycles have occurred
    intent : routing label — either 'sql' or 'chat'
    latency_ms : cumulative wall-clock time spent in LLM calls
    token_usage : token accounting dict (reserved for future use)
    first_failing_query : original SQL that first triggered an error
    first_error : error message from that first failure
    """
    messages: Annotated[List[BaseMessage], operator.add]
    question: str
    sql_query: Optional[str]
    sql_result: Optional[Union[List[dict], str]]
    error: Optional[str]
    revision_count: int
    intent: Optional[str]
    latency_ms: Optional[int]
    token_usage: Optional[dict]
    first_failing_query: Optional[str]
    first_error: Optional[str]
