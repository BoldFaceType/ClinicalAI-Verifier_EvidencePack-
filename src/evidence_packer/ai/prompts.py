SYSTEM_PROMPT = (
    "You are helping prepare a payer appeal evidence packet. "
    "Extract only exact, verbatim evidence sentences from the supplied clinical note. "
    "Do not infer facts. Do not summarize. Do not decide the appeal."
)


def build_user_prompt(
    *,
    denial_text: str,
    strategy_category: str,
    search_terms: list[str],
    note_text: str,
) -> str:
    return (
        f"Denial text: {denial_text}\n"
        f"Evidence strategy: {strategy_category}\n"
        f"Search terms: {', '.join(search_terms)}\n"
        "Return JSON with this shape: {\"excerpts\": [\"verbatim sentence\"]}.\n"
        f"Clinical note:\n{note_text}"
    )
