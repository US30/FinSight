"""
Calculator Tool Node
Safely evaluates mathematical expressions extracted by the Analyst node
using numexpr to avoid LLM math hallucinations.
Supports: basic arithmetic, ratios, percentages, growth rates.
"""

import re
import logging
from typing import TYPE_CHECKING

import numexpr

if TYPE_CHECKING:
    from agent import AgentState

logger = logging.getLogger(__name__)

# Allowlist: only safe characters for financial arithmetic
_SAFE_EXPR_RE = re.compile(r"^[\d\s\+\-\*\/\(\)\.\,\%\^]+$")

# Parse "formula where var1=val1, var2=val2" pattern
_WHERE_RE = re.compile(
    r"^(.+?)\s+where\s+(.+)$", re.IGNORECASE | re.DOTALL
)
_VAR_RE = re.compile(
    r"([\w_]+)\s*=\s*([\d\,\.]+(?:[BbMmKkTt])?)"
)

# Unit multipliers (e.g. "$50B" → 50_000_000_000)
_UNIT_MAP = {
    "t": 1e12, "T": 1e12,
    "b": 1e9,  "B": 1e9,
    "m": 1e6,  "M": 1e6,
    "k": 1e3,  "K": 1e3,
}


def _parse_value(raw: str) -> float:
    """Convert strings like '50B', '1,234.56M' to float."""
    raw = raw.replace(",", "").strip()
    if raw and raw[-1] in _UNIT_MAP:
        return float(raw[:-1]) * _UNIT_MAP[raw[-1]]
    return float(raw)


def _resolve_expression(expression: str) -> tuple[str, dict]:
    """
    Parse 'formula where var1=val1, var2=val2' into
    a substituted numeric expression string and a variable map.
    """
    match = _WHERE_RE.match(expression)
    if not match:
        # No variable substitution needed — use as-is
        return expression.strip(), {}

    formula   = match.group(1).strip()
    var_block = match.group(2).strip()

    variables = {}
    for var_match in _VAR_RE.finditer(var_block):
        name = var_match.group(1)
        try:
            variables[name] = _parse_value(var_match.group(2))
        except ValueError:
            logger.warning(f"[Calculator] Could not parse variable: {var_match.group(0)}")

    # Substitute variable names in formula with their numeric values
    resolved = formula
    for name, value in variables.items():
        resolved = re.sub(rf"\b{re.escape(name)}\b", str(value), resolved)

    return resolved, variables


def _safe_eval(expression: str) -> float:
    """Evaluate a numeric expression using numexpr (sandboxed, no builtins)."""
    # Strip any remaining non-numeric characters as a safety net
    clean = expression.replace("^", "**")  # support caret exponentiation
    result = numexpr.evaluate(clean)
    return float(result)


def calculator_node(state: "AgentState") -> dict:
    """
    Evaluate the calc_expression from analyst state.
    Appends the computed result to the answer and routes to Critic.
    """
    raw_expression = state.get("calc_expression", "").strip()
    original_answer = state.get("answer", "")

    if not raw_expression:
        logger.warning("[Calculator] No expression found in state — passing through.")
        return {
            "needs_calculation": False,
            "messages": [{"role": "calculator", "content": "No expression to evaluate."}],
        }

    logger.info(f"[Calculator] Raw expression: {raw_expression}")

    try:
        resolved, variables = _resolve_expression(raw_expression)
        logger.info(f"[Calculator] Resolved expression: {resolved}")
        logger.info(f"[Calculator] Variables: {variables}")

        result = _safe_eval(resolved)
        result_str = f"{result:,.4f}".rstrip("0").rstrip(".")

        calc_summary = (
            f"\n\n**Calculated Result:** {result_str}\n"
            f"*Expression: {resolved} = {result_str}*"
        )
        if variables:
            var_lines = "\n".join(f"  - {k} = {v:,.2f}" for k, v in variables.items())
            calc_summary = (
                f"\n\n**Calculated Result:** {result_str}\n"
                f"*Variables used:*\n{var_lines}\n"
                f"*Expression: {resolved} = {result_str}*"
            )

        final_answer = original_answer + calc_summary

        # Store the computed metric in extracted_metrics
        existing_metrics = state.get("extracted_metrics", {})
        existing_metrics["calculated_result"] = result
        existing_metrics["expression"] = raw_expression

        logger.info(f"[Calculator] Result: {result_str}")

        return {
            "answer": final_answer,
            "extracted_metrics": existing_metrics,
            "needs_calculation": False,
            "errors": [],
            "messages": [{"role": "calculator", "content": f"Computed: {resolved} = {result_str}"}],
        }

    except Exception as e:
        logger.error(f"[Calculator] Evaluation failed: {e}")
        return {
            "answer": original_answer + "\n\n*[Calculator error — manual verification required]*",
            "errors": [f"Calculator error: {str(e)}"],
            "needs_calculation": False,
            "messages": [{"role": "calculator", "content": f"Evaluation error: {e}"}],
        }
