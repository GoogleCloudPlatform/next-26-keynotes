"""Configuration for the {{AGENT_DISPLAY_NAME}}.

Agent identity, model, and schema. Prompt lives in prompts.py.
When the scenario changes, modify prompts.py and schemas.py instead.
"""

import os

from .prompts import INSTRUCTION  # noqa: F401 — re-exported for backwards compat
from .schemas import MyOutputSchema  # TODO: Import your output schema

# Agent identity
AGENT_NAME = "{{AGENT_MODULE}}"
AGENT_DESCRIPTION = (
    # TODO: Write a clear description of what this agent does.
    "{{AGENT_DISPLAY_NAME}}. "
    "Describe the agent's role, capabilities, and what it produces."
)

# Model configuration
MODEL = os.getenv("{{AGENT_PREFIX}}_MODEL", "gemini-3-flash-preview")

# Structured output schema — set to None if agent uses free-form output
OUTPUT_SCHEMA = MyOutputSchema  # TODO: Set to your Pydantic model or None
