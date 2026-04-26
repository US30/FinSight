"""
Prompt templates for the Researcher node.
"""

RESEARCHER_SYSTEM_PROMPT = (
    "You are a senior quantitative analyst specializing in SEC filings. "
    "Your job is to convert a user's financial question into a precise, "
    "keyword-rich search query optimized for vector similarity search over "
    "10-K and 10-Q documents. "
    "Focus on financial terminology, company names, and metric names. "
    "Return ONLY the search query string — no explanation."
)


def build_researcher_prompt(user_query: str, company: str = "", filing_type: str = "", year: int = 0) -> str:
    context_hints = []
    if company:
        context_hints.append(f"Company: {company}")
    if filing_type:
        context_hints.append(f"Filing type: {filing_type}")
    if year:
        context_hints.append(f"Year: {year}")

    hint_block = "\n".join(context_hints)
    hint_section = f"\nKnown filters:\n{hint_block}\n" if hint_block else ""

    return (
        f"{hint_section}"
        f"\nUser question: {user_query}"
        f"\n\nGenerate the optimal vector search query:"
    )
