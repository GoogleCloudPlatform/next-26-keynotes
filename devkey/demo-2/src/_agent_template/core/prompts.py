"""Prompts for the {{AGENT_DISPLAY_NAME}}.

Agent instruction text extracted from config for readability.
When the scenario changes, modify this file.
"""

INSTRUCTION = """You are the {{AGENT_DISPLAY_NAME}}.

# TODO: Write your agent's instruction prompt here.
# Include:
# - Role description
# - Specific tasks and responsibilities
# - Input/output format expectations
# - Memory usage guidance

**Skills Available:**
You have access to specialized skills:
- '{{SKILL_NAME}}': TODO: Describe what this skill does.

**Workflow:**
1. TODO: Define the agent's workflow steps.

**Output:**
TODO: Describe the expected output format.
"""
