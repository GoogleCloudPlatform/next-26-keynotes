"""System instructions for the Marathon Planner Agent.

Mentions ADK Skills for progressive knowledge loading.
"""

import pathlib

_PROMPT_DIR = pathlib.Path(__file__).parent
INSTRUCTION = (_PROMPT_DIR / "planner-instruction.md").read_text()

