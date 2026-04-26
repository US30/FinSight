"""
Module 4: Agentic Orchestration with LangGraph
Multi-agent state machine with:
  - Researcher → Analyst → Calculator → Critic loop
  - SQLite checkpointer for multi-turn session persistence
  - SQLite query logging for the analytics dashboard
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Annotated, List, Optional
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from typing_extensions import TypedDict

from nodes import researcher_node, analyst_node, calculator_node, critic_node

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AGENT_STATE_DB = "./agent_state.db"
AGENT_LOGS_DB  = "./agent_logs.db"


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    # Core conversation
    messages:          Annotated[List[dict], operator.add]
    query:             str
    answer:            str

    # Filters inferred from the query
    current_company:   str
    filing_type:       str
    year:              int

    # Retrieved context
    context_docs:      list           # List[Document] — not annotated to avoid serialization issues

    # Analyst routing flags
    needs_calculation: bool
    calc_expression:   str
    missing_data:      bool

    # Critic routing flags
    validated:         bool
    retry_count:       int

    # Output
    extracted_metrics: dict
    errors:            List[str]

    # Session
    thread_id:         str


# ---------------------------------------------------------------------------
# Query logger (writes to agent_logs.db for the analytics layer)
# ---------------------------------------------------------------------------

def _init_logs_db() -> None:
    with sqlite3.connect(AGENT_LOGS_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_queries (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT NOT NULL,
                thread_id     TEXT NOT NULL,
                company       TEXT,
                filing_type   TEXT,
                year          INTEGER,
                query         TEXT NOT NULL,
                answer        TEXT NOT NULL,
                metrics_json  TEXT,
                retry_count   INTEGER DEFAULT 0,
                status        TEXT DEFAULT 'success'
            )
        """)
        conn.commit()


def log_query(state: AgentState) -> None:
    """Persist a completed agent run to the logs database."""
    _init_logs_db()

    answer  = state.get("answer", "")
    status  = "insufficient_data" if "INSUFFICIENT_DATA" in answer.upper() else "success"
    if state.get("errors"):
        status = "error"

    with sqlite3.connect(AGENT_LOGS_DB) as conn:
        conn.execute(
            """
            INSERT INTO agent_queries
                (timestamp, thread_id, company, filing_type, year,
                 query, answer, metrics_json, retry_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                state.get("thread_id", "unknown"),
                state.get("current_company", ""),
                state.get("filing_type", ""),
                state.get("year", 0),
                state.get("query", ""),
                answer,
                json.dumps(state.get("extracted_metrics", {})),
                state.get("retry_count", 0),
                status,
            ),
        )
        conn.commit()
    logger.info(f"[Logger] Query logged with status='{status}'.")


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def route_after_analyst(state: AgentState) -> str:
    if state.get("missing_data"):
        return "researcher"
    if state.get("needs_calculation"):
        return "calculator"
    return "critic"


def route_after_critic(state: AgentState) -> str:
    if state.get("validated"):
        return END
    return "researcher"


# ---------------------------------------------------------------------------
# Terminal logging node (runs just before END)
# ---------------------------------------------------------------------------

def logger_node(state: AgentState) -> dict:
    """Write the completed run to agent_logs.db."""
    log_query(state)
    return {}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst",    analyst_node)
    graph.add_node("calculator", calculator_node)
    graph.add_node("critic",     critic_node)
    graph.add_node("log",        logger_node)

    # Entry point
    graph.set_entry_point("researcher")

    # Fixed edges
    graph.add_edge("researcher", "analyst")
    graph.add_edge("calculator", "critic")
    graph.add_edge("log",        END)

    # Conditional edges
    graph.add_conditional_edges(
        "analyst",
        route_after_analyst,
        {
            "researcher": "researcher",
            "calculator": "calculator",
            "critic":     "critic",
        },
    )
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "researcher": "researcher",
            END:          "log",
        },
    )

    return graph


def compile_app(checkpointer: Optional[SqliteSaver] = None):
    """
    Compile the LangGraph application.
    If no checkpointer is provided, creates a default SQLite checkpointer.
    """
    if checkpointer is None:
        checkpointer = SqliteSaver.from_conn_string(AGENT_STATE_DB)
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# Public helper: run a single query
# ---------------------------------------------------------------------------

def run_query(
    query: str,
    thread_id: str,
    company: str = "",
    filing_type: str = "",
    year: int = 0,
    app=None,
) -> dict:
    """
    Run the agent for a single user query and return the final state.

    Args:
        query:        User's natural language financial question.
        thread_id:    Session UUID (for multi-turn persistence).
        company:      Optional ticker filter (e.g. "AAPL").
        filing_type:  Optional filing filter ("10-K" or "10-Q").
        year:         Optional year filter.
        app:          Pre-compiled LangGraph app (compiled once and reused).
    """
    if app is None:
        app = compile_app()

    initial_state: AgentState = {
        "messages":          [],
        "query":             query,
        "answer":            "",
        "current_company":   company,
        "filing_type":       filing_type,
        "year":              year,
        "context_docs":      [],
        "needs_calculation": False,
        "calc_expression":   "",
        "missing_data":      False,
        "validated":         False,
        "retry_count":       0,
        "extracted_metrics": {},
        "errors":            [],
        "thread_id":         thread_id,
    }

    config = {"configurable": {"thread_id": thread_id}}
    final_state = app.invoke(initial_state, config=config)
    return final_state


# ---------------------------------------------------------------------------
# Entry point (CLI smoke test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uuid

    compiled_app = compile_app()
    session_id   = str(uuid.uuid4())

    test_queries = [
        ("What was Apple's total revenue in 2023?",          "AAPL", "10-K", 2023),
        ("Calculate JPMorgan's Debt-to-Equity ratio for 2022.", "JPM", "10-K", 2022),
    ]

    for q, ticker, ftype, yr in test_queries:
        print(f"\n{'='*60}")
        print(f"Query   : {q}")
        print(f"Filters : {ticker} | {ftype} | {yr}")
        print("="*60)

        result = run_query(
            query=q,
            thread_id=session_id,
            company=ticker,
            filing_type=ftype,
            year=yr,
            app=compiled_app,
        )

        print(f"\nAnswer:\n{result.get('answer', 'N/A')}")
        print(f"\nRetries : {result.get('retry_count', 0)}")
        print(f"Metrics : {result.get('extracted_metrics', {})}")
        print(f"Errors  : {result.get('errors', [])}")
