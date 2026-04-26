"""
Researcher Node
Converts the user query into an optimised vector search query,
retrieves top-k documents from Qdrant, and updates agent state.
"""

import logging
from typing import TYPE_CHECKING

from langchain.schema import Document

if TYPE_CHECKING:
    from agent import AgentState

logger = logging.getLogger(__name__)

TOP_K = 8  # default documents to retrieve


def researcher_node(state: "AgentState") -> dict:
    """
    1. Use the LLM to rewrite the user query into an optimal search query.
    2. Run similarity search against Qdrant with any known metadata filters.
    3. Return updated state with retrieved context_docs.
    """
    from vector_store import load_vector_store, similarity_search
    from llm_engine import get_llm
    from prompts import RESEARCHER_SYSTEM_PROMPT, build_researcher_prompt

    query        = state["query"]
    company      = state.get("current_company", "")
    filing_type  = state.get("filing_type", "")
    year         = state.get("year", 0)
    retry_count  = state.get("retry_count", 0)

    llm = get_llm()

    # On retries, build a refinement hint from missing data errors
    missing_items = state.get("errors", [])
    if retry_count > 0 and missing_items:
        from prompts.analyst_prompt import build_refinement_prompt
        search_query_prompt = build_refinement_prompt(query, missing_items)
    else:
        search_query_prompt = (
            RESEARCHER_SYSTEM_PROMPT
            + build_researcher_prompt(query, company, filing_type, year)
        )

    logger.info(f"[Researcher] Generating search query (retry={retry_count})...")
    search_query = llm.invoke(search_query_prompt).strip()
    logger.info(f"[Researcher] Search query: {search_query}")

    vs = load_vector_store()

    # Numeric queries benefit from table-first retrieval
    numeric_keywords = {"ratio", "revenue", "income", "debt", "equity", "margin",
                        "eps", "ebitda", "cash", "assets", "liabilities", "growth"}
    prefer_tables = any(kw in query.lower() for kw in numeric_keywords)

    docs: list[Document] = similarity_search(
        query=search_query,
        vector_store=vs,
        k=TOP_K,
        filter_ticker=company or None,
        filter_filing_type=filing_type or None,
        filter_year=year or None,
        prefer_tables=prefer_tables,
    )

    logger.info(f"[Researcher] Retrieved {len(docs)} documents.")

    return {
        "context_docs": docs,
        "messages": [{"role": "researcher", "content": f"Retrieved {len(docs)} documents for query: {search_query}"}],
    }
