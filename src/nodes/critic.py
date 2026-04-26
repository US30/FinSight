"""
Critic Node (Self-Correction)
Verifies the proposed answer against the raw retrieved context.
Triggers a retry loop if hallucination is detected (max 2 retries).
"""

import re
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import AgentState

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

_VERDICT_RE = re.compile(r"VERDICT:\s*(PASS|FAIL)", re.IGNORECASE)
_REASON_RE  = re.compile(r"REASON:\s*(.+?)(?:\n|$)", re.IGNORECASE)
_UNSUPPORTED_RE = re.compile(r"UNSUPPORTED_CLAIMS:\s*(.+?)(?:\n|$)", re.IGNORECASE)


def _format_context(docs: list) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        m = doc.metadata
        citation = (
            f"[{m.get('company_ticker','?')} | "
            f"{m.get('filing_type','?')} | "
            f"{m.get('year','?')} | "
            f"{m.get('section','?')}]"
        )
        parts.append(f"--- Source {i} {citation} ---\n{doc.page_content}")
    return "\n\n".join(parts)


def critic_node(state: "AgentState") -> dict:
    """
    1. Ask the LLM to verify the proposed answer against source context.
    2. PASS  → mark validated, proceed to END.
    3. FAIL  → increment retry_count; if under MAX_RETRIES, route back to Researcher.
               If retry limit reached, return INSUFFICIENT_DATA.
    """
    from llm_engine import get_llm
    from prompts import CRITIC_SYSTEM_PROMPT, build_critic_prompt

    answer      = state.get("answer", "")
    query       = state["query"]
    docs        = state.get("context_docs", [])
    retry_count = state.get("retry_count", 0)

    # If the analyst already flagged INSUFFICIENT_DATA, skip LLM call
    if answer.strip().upper() == "INSUFFICIENT_DATA":
        logger.info("[Critic] Answer is INSUFFICIENT_DATA — passing through.")
        return {
            "validated": True,
            "messages": [{"role": "critic", "content": "INSUFFICIENT_DATA confirmed — no hallucination check needed."}],
        }

    context = _format_context(docs)
    prompt  = CRITIC_SYSTEM_PROMPT + "\n\n" + build_critic_prompt(query, answer, context)

    llm = get_llm()
    logger.info("[Critic] Invoking LLM for hallucination check...")
    raw_verdict = llm.invoke(prompt).strip()
    logger.info(f"[Critic] Verdict response: {raw_verdict[:300]}")

    # Parse verdict
    verdict_match = _VERDICT_RE.search(raw_verdict)
    verdict = verdict_match.group(1).upper() if verdict_match else "FAIL"

    reason_match = _REASON_RE.search(raw_verdict)
    reason = reason_match.group(1).strip() if reason_match else "No reason provided."

    unsupported_match = _UNSUPPORTED_RE.search(raw_verdict)
    unsupported = unsupported_match.group(1).strip() if unsupported_match else "None"

    logger.info(f"[Critic] Verdict={verdict} | Reason={reason} | Unsupported={unsupported}")

    if verdict == "PASS":
        return {
            "validated": True,
            "errors": [],
            "messages": [{"role": "critic", "content": f"Answer validated. Reason: {reason}"}],
        }

    # FAIL branch
    new_retry_count = retry_count + 1

    if new_retry_count >= MAX_RETRIES:
        logger.warning(f"[Critic] Max retries ({MAX_RETRIES}) reached. Returning INSUFFICIENT_DATA.")
        return {
            "validated": True,   # mark True to exit loop
            "answer": "INSUFFICIENT_DATA",
            "retry_count": new_retry_count,
            "errors": [f"Hallucination detected after {new_retry_count} retries: {unsupported}"],
            "messages": [{"role": "critic", "content": f"Retry limit reached. Unsupported claims: {unsupported}"}],
        }

    logger.info(f"[Critic] Hallucination detected (retry {new_retry_count}/{MAX_RETRIES}). Re-routing to Researcher.")
    return {
        "validated": False,
        "retry_count": new_retry_count,
        "errors": [f"Unsupported claims: {unsupported}"],
        "messages": [{"role": "critic", "content": f"FAIL — retry {new_retry_count}. Unsupported: {unsupported}"}],
    }
