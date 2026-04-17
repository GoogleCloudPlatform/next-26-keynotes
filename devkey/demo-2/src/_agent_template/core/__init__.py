"""{{AGENT_DISPLAY_NAME}} agent definition.

Exports root_agent for use by the executor and local server.
"""

try:
    from .agent import root_agent
    from .config import AGENT_NAME, MODEL

    __all__ = ["root_agent", "AGENT_NAME", "MODEL"]
except Exception:
    pass
