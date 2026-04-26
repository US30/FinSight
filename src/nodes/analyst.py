"""
Analyst Node
Reads retrieved context, extracts numeric values, and either:
  - Sets needs_calculation=True with a formula for the Calculator node, or
  - Sets missing_data=True to loop back to the Researcher node, or
  - Produces a direct answer for the Critic node.
"""

import re
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import AgentState

logger = logging.getLogger(__name__)

# Pattern to detect NEEDS_CALCULATION signal from the LLM
_NEEDS_CALC_RE = re.compile(
    r"NEEDS_CALCULATION:\s*(.+?)(?:\n|$)", re.IGNORECASE
)


def _format_context(docs: list) -> str:
    """Render retrieved documents into a single context block with source citations."""
    parts = []
    for i, doc in enumerate(docs, 1):
        m = doc.metadata
        citation = (
            f"[{m.get('company_ticker','?')} | "
            f"{m.get('filing_type','?')} | "
            f"{m.get('year','?')} | "
            f"{m.get('section','?')} | "
            f"type={m.get('chunk_type','?')}]"
        )
        parts.append(f"--- Source {i} {citation} ---\n{doc.page_content}")
    return "\n\n".join(parts)


def analyst_node(state: "AgentState") -> dict:
    """
    Analyse retrieved context against the user query.
    Returns updated state fields: answer, needs_calculation, calc_expression,
    missing_data, errors, extracted_metrics.
    """
    from llm_engine import get_llm
    from prompts import ANALYST_SYSTEM_PROMPT, build_analyst_prompt

    query    = state["query"]
    docs     = state.get("context_docs", [])

    if not docs:
        logger.warning("[Analyst] No context documents available — flagging missing_data.")
        return {
            "missing_data": True,
            "errors": ["No documents retrieved from vector store."],
            "messages": [{"role": "analyst", "content": "No context available. Requesting re-retrieval."}],
        }

    context = _format_context(docs)
    prompt  = ANALYST_SYSTEM_PROMPT + "\n\n" + build_analyst_prompt(query, context)

    llm = get_llm()
    logger.info("[Analyst] Invoking LLM for analysis...")
    raw_answer = llm.invoke(prompt).strip()
    logger.info(f"[Analyst] Raw answer: {raw_answer[:300]}...")

    # --- Route 1: INSUFFICIENT_DATA ---
    if "INSUFFICIENT_DATA" in raw_answer.upper():
        missing_items = [query]
        logger.info("[Analyst] LLM signalled INSUFFICIENT_DATA.")
        return {
            "missing_data": True,
            "errors": missing_items,
            "answer": "INSUFFICIENT_DATA",
            "messages": [{"role": "analyst", "content": "Insufficient data found. Requesting refined retrieval."}],
        }

    # --- Route 2: NEEDS_CALCULATION ---
    calc_match = _NEEDS_CALC_RE.search(raw_answer)
    if calc_match:
        calc_expression = calc_match.group(1).strip()
        logger.info(f"[Analyst] Calculation needed: {calc_expression}")
        return {
            "needs_calculation": True,
            "calc_expression": calc_expression,
            "answer": raw_answer,
            "missing_data": False,
            "errors": [],
            "messages": [{"role": "analyst", "content": f"Calculation required: {calc_expression}"}],
        }

    # --- Route 3: Direct answer — pass to Critic ---
    logger.info("[Analyst] Direct answer produced — routing to Critic.")
    return {
        "answer": raw_answer,
        "needs_calculation": False,
        "missing_data": False,
        "errors": [],
        "messages": [{"role": "analyst", "content": raw_answer}],
    }
