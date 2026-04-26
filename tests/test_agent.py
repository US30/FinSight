"""
Tests for Module 4: agent.py
Tests state routing logic, calculator evaluation, critic verdicts,
and SQLite logging — all without loading real models or Qdrant.
"""

import json
import os
import sqlite3
import sys
from unittest.mock import MagicMock, patch

import pytest
from langchain.schema import Document

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_state(**overrides) -> dict:
    base = {
        "messages":          [],
        "query":             "What is AAPL revenue in 2023?",
        "answer":            "",
        "current_company":   "AAPL",
        "filing_type":       "10-K",
        "year":              2023,
        "context_docs":      [],
        "needs_calculation": False,
        "calc_expression":   "",
        "missing_data":      False,
        "validated":         False,
        "retry_count":       0,
        "extracted_metrics": {},
        "errors":            [],
        "thread_id":         "test-thread-001",
    }
    base.update(overrides)
    return base


def _make_doc(chunk_type="text", ticker="AAPL") -> Document:
    return Document(
        page_content="Total revenue was $383 billion for fiscal 2023.",
        metadata={
            "company_ticker": ticker,
            "filing_type":    "10-K",
            "year":           2023,
            "section":        "Financial Statements",
            "chunk_type":     chunk_type,
        },
    )


# ---------------------------------------------------------------------------
# Graph routing functions
# ---------------------------------------------------------------------------

def test_route_after_analyst_missing_data():
    from agent import route_after_analyst
    state = _make_state(missing_data=True)
    assert route_after_analyst(state) == "researcher"


def test_route_after_analyst_needs_calculation():
    from agent import route_after_analyst
    state = _make_state(needs_calculation=True, missing_data=False)
    assert route_after_analyst(state) == "calculator"


def test_route_after_analyst_to_critic():
    from agent import route_after_analyst
    state = _make_state(needs_calculation=False, missing_data=False)
    assert route_after_analyst(state) == "critic"


def test_route_after_critic_validated():
    from agent import route_after_critic
    from langgraph.graph import END
    state = _make_state(validated=True)
    assert route_after_critic(state) == END


def test_route_after_critic_not_validated():
    from agent import route_after_critic
    state = _make_state(validated=False)
    assert route_after_critic(state) == "researcher"


# ---------------------------------------------------------------------------
# Calculator node
# ---------------------------------------------------------------------------

def test_calculator_simple_expression():
    from nodes.calculator import calculator_node
    state = _make_state(
        calc_expression="total_debt / total_equity where total_debt=50000000000, total_equity=25000000000",
        answer="Analyst extracted the values.",
    )
    result = calculator_node(state)
    assert result["needs_calculation"] is False
    assert "2.0" in result["answer"] or "2" in result["answer"]
    assert result["extracted_metrics"]["calculated_result"] == pytest.approx(2.0)


def test_calculator_with_unit_suffixes():
    from nodes.calculator import calculator_node
    state = _make_state(
        calc_expression="revenue / net_income where revenue=383B, net_income=97B",
        answer="Base answer.",
    )
    result = calculator_node(state)
    assert result["needs_calculation"] is False
    expected = 383e9 / 97e9
    assert result["extracted_metrics"]["calculated_result"] == pytest.approx(expected, rel=1e-3)


def test_calculator_empty_expression():
    from nodes.calculator import calculator_node
    state = _make_state(calc_expression="", answer="Some answer.")
    result = calculator_node(state)
    assert result["needs_calculation"] is False
    # Should pass through without error
    assert "expression" not in result.get("errors", [])


def test_calculator_invalid_expression_returns_error():
    from nodes.calculator import calculator_node
    state = _make_state(
        calc_expression="import os; os.system('rm -rf /')",
        answer="Base answer.",
    )
    result = calculator_node(state)
    # Should catch the error gracefully
    assert result["needs_calculation"] is False
    assert len(result.get("errors", [])) > 0 or "error" in result["answer"].lower()


# ---------------------------------------------------------------------------
# Critic node
# ---------------------------------------------------------------------------

def test_critic_passes_on_pass_verdict():
    from nodes.critic import critic_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = (
        "VERDICT: PASS\nREASON: All values are supported.\nUNSUPPORTED_CLAIMS: None"
    )

    with (
        patch("nodes.critic.get_llm", return_value=mock_llm),
        patch("nodes.critic.build_critic_prompt", return_value="prompt"),
        patch("nodes.critic.CRITIC_SYSTEM_PROMPT", ""),
    ):
        state = _make_state(
            answer="AAPL revenue was $383B in 2023.",
            context_docs=[_make_doc()],
        )
        result = critic_node(state)

    assert result["validated"] is True
    assert result["errors"] == []


def test_critic_fails_and_increments_retry():
    from nodes.critic import critic_node

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = (
        "VERDICT: FAIL\nREASON: Value not found in context.\nUNSUPPORTED_CLAIMS: $383B"
    )

    with (
        patch("nodes.critic.get_llm", return_value=mock_llm),
        patch("nodes.critic.build_critic_prompt", return_value="prompt"),
        patch("nodes.critic.CRITIC_SYSTEM_PROMPT", ""),
    ):
        state = _make_state(
            answer="AAPL revenue was $383B in 2023.",
            context_docs=[_make_doc()],
            retry_count=0,
        )
        result = critic_node(state)

    assert result["validated"] is False
    assert result["retry_count"] == 1


def test_critic_returns_insufficient_data_at_max_retries():
    from nodes.critic import critic_node, MAX_RETRIES

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = (
        "VERDICT: FAIL\nREASON: Still not found.\nUNSUPPORTED_CLAIMS: $383B"
    )

    with (
        patch("nodes.critic.get_llm", return_value=mock_llm),
        patch("nodes.critic.build_critic_prompt", return_value="prompt"),
        patch("nodes.critic.CRITIC_SYSTEM_PROMPT", ""),
    ):
        state = _make_state(
            answer="AAPL revenue was $383B in 2023.",
            context_docs=[_make_doc()],
            retry_count=MAX_RETRIES - 1,   # one more will hit the limit
        )
        result = critic_node(state)

    assert result["validated"] is True
    assert result["answer"] == "INSUFFICIENT_DATA"


def test_critic_skips_llm_for_insufficient_data_answer():
    from nodes.critic import critic_node

    mock_llm = MagicMock()

    with patch("nodes.critic.get_llm", return_value=mock_llm):
        state = _make_state(answer="INSUFFICIENT_DATA", context_docs=[])
        result = critic_node(state)

    mock_llm.invoke.assert_not_called()
    assert result["validated"] is True


# ---------------------------------------------------------------------------
# SQLite logging
# ---------------------------------------------------------------------------

def test_log_query_writes_to_db(tmp_path, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "AGENT_LOGS_DB", str(tmp_path / "test_logs.db"))

    state = _make_state(
        answer="AAPL revenue was $383B.",
        extracted_metrics={"revenue": 383e9},
        retry_count=0,
    )
    agent.log_query(state)

    with sqlite3.connect(str(tmp_path / "test_logs.db")) as conn:
        rows = conn.execute("SELECT * FROM agent_queries").fetchall()

    assert len(rows) == 1
    assert rows[0][6] == state["query"]    # query column
    assert rows[0][10] == "success"        # status column


def test_log_query_status_insufficient_data(tmp_path, monkeypatch):
    import agent
    monkeypatch.setattr(agent, "AGENT_LOGS_DB", str(tmp_path / "test_logs.db"))

    state = _make_state(answer="INSUFFICIENT_DATA")
    agent.log_query(state)

    with sqlite3.connect(str(tmp_path / "test_logs.db")) as conn:
        row = conn.execute("SELECT status FROM agent_queries").fetchone()

    assert row[0] == "insufficient_data"
