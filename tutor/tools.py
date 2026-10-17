from langchain_core.tools import tool

GLOSSARY = {
    "send api": "A LangGraph feature that lets one node fan out work to a dynamic number of parallel workers, each with its own input.",
    "handoff": "A multi-agent pattern where agents pass control to each other, and any agent can reply directly to the user.",
    "checkpointer": "A component that saves a graph's state after each step so a conversation can continue later under the same thread ID.",
}


@tool
def list_terms() -> str:
    """List every term in the course glossary. Use this when the learner asks
    which terms are available, or when you are unsure of an exact term name."""
    print("[tool ran] list_terms")
    return ", ".join(sorted(GLOSSARY))


@tool
def lookup_term(term: str) -> str:
    """Look up the definition of one agentic AI term in the course glossary.
    Use this whenever the learner asks what a specific term means."""
    print("[tool ran] lookup_term, term =", repr(term))
    return GLOSSARY.get(term.lower().strip(), f"No glossary entry for '{term}'.")