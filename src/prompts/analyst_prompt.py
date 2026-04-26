"""
Prompt templates for the Analyst node.
"""

ANALYST_SYSTEM_PROMPT = (
    "You are a senior quantitative analyst. "
    "You only rely on the provided SEC filing context. "
    "If a value is not found in the text, you must output 'INSUFFICIENT_DATA' rather than guessing. "
    "You must cite your sources using metadata (company_ticker, filing_type, year, section). "
    "When extracting numbers for calculations, return them as exact figures with units."
)


def build_analyst_prompt(user_query: str, context: str) -> str:
    return (
        f"## Retrieved SEC Filing Context\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"## User Question\n\n"
        f"{user_query}\n\n"
        f"## Instructions\n\n"
        f"1. Answer the question using ONLY the context above.\n"
        f"2. If the question requires a calculation (ratio, percentage, growth rate), "
        f"extract the raw numbers and label them clearly as:\n"
        f"   NEEDS_CALCULATION: <formula> where <var1>=<value1>, <var2>=<value2>\n"
        f"3. If required data is missing from the context, output exactly: INSUFFICIENT_DATA\n"
        f"4. Cite sources as: [ticker | filing_type | year | section]\n\n"
        f"## Analysis:"
    )


def build_refinement_prompt(original_query: str, missing_items: list) -> str:
    missing_str = ", ".join(missing_items)
    return (
        f"The following data points were not found in the initial search: {missing_str}.\n"
        f"Original question: {original_query}\n\n"
        f"Generate a more targeted search query to find the missing values:"
    )
