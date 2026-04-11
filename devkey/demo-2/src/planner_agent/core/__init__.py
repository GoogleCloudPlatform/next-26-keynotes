"""Marathon Planner Agent — core agent module.

Exports the root_agent for use by runtime and tests.
"""

from .agent import root_agent
from .config import AGENT_NAME, MODEL, AGENT_DESCRIPTION, OUTPUT_SCHEMA

__all__ = ["root_agent", "AGENT_NAME", "MODEL", "AGENT_DESCRIPTION", "OUTPUT_SCHEMA"]
