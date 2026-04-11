"""Prompts for the Evaluator Agent.

Consolidated system instructions incorporating evaluation methodology, 
score interpretation, and improvement strategy.
"""

import pathlib

_PROMPT_DIR = pathlib.Path(__file__).parent
INSTRUCTION = (_PROMPT_DIR / "instruction.md").read_text()

