"""
Prompt templates for the Critic node.
"""

CRITIC_SYSTEM_PROMPT = (
    "You are a strict financial fact-checker. "
    "Your sole job is to verify that every numerical claim in a proposed answer "
    "is directly supported by the provided source context. "
    "You do not add information — you only validate or reject."
)


def build_critic_prompt(user_query: str, proposed_answer: str, context: str) -> str:
    return (
        f"## Source Context (Ground Truth)\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"## User Question\n\n"
        f"{user_query}\n\n"
        f"## Proposed Answer to Verify\n\n"
        f"{proposed_answer}\n\n"
        f"---\n\n"
        f"## Verification Task\n\n"
        f"Check every numerical value and factual claim in the proposed answer against the source context above.\n\n"
        f"Respond in this exact format:\n"
        f"VERDICT: PASS or FAIL\n"
        f"REASON: <one sentence explanation>\n"
        f"UNSUPPORTED_CLAIMS: <comma-separated list of claims not found in context, or 'None'>\n\n"
        f"## Verdict:"
    )
