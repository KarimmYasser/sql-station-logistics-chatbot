"""
Graph node implementations.
Each public function in this module is registered as a LangGraph node
and receives / returns an AgentState dictionary.
"""

import sqlite3
import re
import os
import time

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from .state import AgentState
from .prompts import (
    ROUTER_PROMPT,
    SYSTEM_PROMPT,
    CHAT_PROMPT,
    RESPONSE_PROMPT,
    REPLAN_PROMPT,
    get_schema_string,
)

load_dotenv()

# ── LLM provider configuration ──────────────────────────────────
_PROVIDER_KEY = os.getenv("PROVIDER", "lmstudio").lower()
_MODEL_ID = os.getenv("MODEL_NAME", "google/gemma-3n-e4b")
_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_LMSTUDIO_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
_DB_FILEPATH = 'space_station_supply.db'


def _create_llm():
    """Instantiate the correct chat model based on the PROVIDER env var."""
    if _PROVIDER_KEY == "openai":
        return ChatOpenAI(model=_MODEL_ID, temperature=0)
    elif _PROVIDER_KEY == "groq":
        return ChatGroq(model=_MODEL_ID, temperature=0)
    elif _PROVIDER_KEY == "lmstudio":
        return ChatOpenAI(
            model=_MODEL_ID, temperature=0,
            base_url=_LMSTUDIO_URL, api_key="lm-studio",
        )
    else:
        return ChatOllama(
            model=_MODEL_ID, temperature=0,
            base_url=_OLLAMA_URL,
        )


_llm = _create_llm()


# ── Utility ──────────────────────────────────────────────────────
def _parse_sql_from_response(raw_text: str) -> str:
    """
    Strip surrounding markdown fences and conversational fluff
    from an LLM reply, returning only the SQL statement.
    """
    # Attempt 1: look for a fenced code block
    fence_match = re.search(
        r'```(?:sql)?\n?(.*?)\n?```', raw_text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        return fence_match.group(1).strip()

    # Attempt 2: find the first SQL keyword and grab everything after it
    keyword_pattern = r'(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|DROP)'
    kw_match = re.search(rf'\b{keyword_pattern}\b', raw_text, re.IGNORECASE)
    if kw_match:
        fragment = raw_text[kw_match.start():].strip()

        semicolon = re.search(r';', fragment)
        if semicolon:
            return fragment[:semicolon.end()].strip()

        # Fall back to line-by-line until we hit conversational text
        kept_lines = []
        noise_prefixes = r'^(This|I hope|Let me|Note|You can)'
        for line in fragment.split('\n'):
            if re.match(noise_prefixes, line.strip(), re.IGNORECASE):
                break
            kept_lines.append(line)
        return '\n'.join(kept_lines).strip()

    return raw_text.strip()


# ── Node functions ───────────────────────────────────────────────

def router_node(state: AgentState):
    """Decide whether the user's message requires a DB query or casual chat."""
    print("\n--- [NODE: ROUTER] ---")
    tick = time.time()

    prompt_messages = [
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=state['question']),
    ]
    llm_reply = _llm.invoke(prompt_messages)

    reply_text = llm_reply.content.strip().lower()
    detected_intent = 'sql' if 'sql' in reply_text else 'chat'
    print(f"Detected Intent: {detected_intent}")

    elapsed = int((time.time() - tick) * 1000)
    result = {"intent": detected_intent, "latency_ms": elapsed}

    if detected_intent == 'chat':
        result["sql_query"] = None
        result["sql_result"] = None
        result["error"] = None

    return result


def chat_node(state: AgentState):
    """Produce a conversational greeting / small-talk reply."""
    print("--- [NODE: CHAT] ---")
    tick = time.time()

    prompt_messages = [
        SystemMessage(content=CHAT_PROMPT),
        HumanMessage(content=state['question']),
    ]
    llm_reply = _llm.invoke(prompt_messages)
    elapsed = int((time.time() - tick) * 1000)

    return {"messages": [llm_reply], "latency_ms": elapsed}


def sql_generator_node(state: AgentState):
    """Translate the natural-language question into a SQLite query."""
    print("--- [NODE: SQL GENERATOR] ---")
    tick = time.time()

    schema_text = get_schema_string(_DB_FILEPATH)
    prompt_messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(schema=schema_text)),
        HumanMessage(content=state['question']),
    ]
    llm_reply = _llm.invoke(prompt_messages)
    generated_sql = _parse_sql_from_response(llm_reply.content)
    print(f"Generated SQL: {generated_sql}")

    elapsed = int((time.time() - tick) * 1000)
    return {
        "sql_query": generated_sql,
        "revision_count": 0,
        "latency_ms": elapsed,
    }


def sql_executor_node(state: AgentState):
    """Run the current SQL statement against the local database."""
    print("--- [NODE: SQL EXECUTOR] ---")
    tick = time.time()

    query_text = state['sql_query']
    print(f"Executing: {query_text}")

    try:
        conn = sqlite3.connect(_DB_FILEPATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query_text)
        fetched = cur.fetchall()
        rows_as_dicts = [dict(r) for r in fetched]
        conn.close()

        print(f"Success. Rows found: {len(rows_as_dicts)}")
        elapsed = int((time.time() - tick) * 1000)
        return {
            "sql_result": rows_as_dicts,
            "error": None,
            "latency_ms": elapsed,
        }

    except Exception as exc:
        print(f"Failed: {exc}")
        elapsed = int((time.time() - tick) * 1000)
        payload = {"error": str(exc), "latency_ms": elapsed}

        if state.get("revision_count", 0) == 0:
            payload["first_failing_query"] = query_text
            payload["first_error"] = str(exc)

        return payload


def sql_corrector_node(state: AgentState):
    """Attempt to fix a broken SQL statement using the LLM."""
    print("--- [NODE: SQL CORRECTOR] ---")
    tick = time.time()

    schema_text = get_schema_string(_DB_FILEPATH)
    correction_context = REPLAN_PROMPT.format(
        error=state['error'],
        question=state['question'],
        sql_query=state['sql_query'],
        schema=schema_text,
    )

    architect_system = SystemMessage(
        content=(
            "You are a Master Data Architect fixing a broken SQLite query. "
            "Return ONLY raw SQLite code. No markdown, no explanations."
        )
    )
    llm_reply = _llm.invoke([architect_system, HumanMessage(content=correction_context)])
    corrected_sql = _parse_sql_from_response(llm_reply.content)

    # Guard against hallucinated non-SQL output
    hallucination_markers = (
        "Question:", "Let ", "Solve ", "Answer:", "I apologize", "floor("
    )
    if any(marker in corrected_sql for marker in hallucination_markers):
        print("Hallucination detected. Breaking loop.")
        return {
            "revision_count": 4,
            "error": "The system was unable to generate a valid database query.",
            "latency_ms": int((time.time() - tick) * 1000),
        }

    print(f"Corrected SQL: {corrected_sql}")
    elapsed = int((time.time() - tick) * 1000)
    return {
        "sql_query": corrected_sql,
        "revision_count": state['revision_count'] + 1,
        "latency_ms": elapsed,
    }


def responder_node(state: AgentState):
    """Build the final human-readable answer from the query results."""
    print("--- [NODE: RESPONDER] ---")
    tick = time.time()

    # Chat messages were already produced by chat_node
    if state.get('intent') == 'chat':
        return {"latency_ms": int((time.time() - tick) * 1000)}

    # Surface execution errors directly
    if state.get('error'):
        warning = f"Warning: I encountered a disruption accessing the registry: {state['error']}"
        return {
            "messages": [AIMessage(content=warning)],
            "latency_ms": int((time.time() - tick) * 1000),
        }

    # Format DB rows for the summarisation prompt
    fetched_data = state.get('sql_result', [])
    data_text = str(fetched_data) if fetched_data else "No records found."

    summarise_prompt = RESPONSE_PROMPT.format(
        question=state['question'],
        sql_query=state['sql_query'],
        sql_result=data_text,
    )
    llm_reply = _llm.invoke([HumanMessage(content=summarise_prompt)])
    body = llm_reply.content.strip()

    # Strip report delimiters injected by the LLM
    body = re.sub(r'\[\s*REPORT\s+START\s*\]', '', body, flags=re.IGNORECASE)
    body = re.sub(r'\[\s*REPORT\s+END\s*\]', '', body, flags=re.IGNORECASE)
    body = re.sub(r'#+\s*REPORT\s+(START|END)\s*#*', '', body, flags=re.IGNORECASE)
    body = body.strip()

    elapsed = int((time.time() - tick) * 1000)
    return {
        "messages": [AIMessage(content=body)],
        "latency_ms": state.get("latency_ms", 0) + elapsed,
    }
