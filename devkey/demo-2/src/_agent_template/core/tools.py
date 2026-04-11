"""Computation tools for the {{AGENT_DISPLAY_NAME}}.

FunctionTools for computation the LLM cannot do directly.
Procedural knowledge (step-by-step instructions, reference data)
lives in skills/ instead.
"""


# TODO: Implement your agent's FunctionTools here.
#
# FunctionTools are for computation: math, data lookups, API calls.
# Skills are for procedure: "Step 1: do X, Step 2: do Y".
#
# Example:
#
# def lookup_information(query: str) -> dict:
#     """Look up information based on a query.
#
#     Args:
#         query: The search query
#
#     Returns:
#         dict with search results
#     """
#     return {"results": [...]}


def get_tools() -> list:
    """Return the FunctionTools for this agent.

    Returns:
        List of callable tools for this agent.
    """
    return [
        # TODO: Add your FunctionTools here
    ]
