"""Marathon Planner Agent — LlmAgent wiring.

Wires config + prompts + tools + skills into the LlmAgent.
To change the scenario, edit config.py, prompts.py, and tools.py.
"""

import os

import vertexai
from google.adk.agents import LlmAgent

from .config import AGENT_NAME, AGENT_DESCRIPTION, MODEL, OUTPUT_SCHEMA
from .prompts import INSTRUCTION
from .tools import get_tools
from ..services.memory_manager import auto_save_memories

# Initialize Vertex AI - required for LLM access
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
if project_id:
    vertexai.init(project=project_id, location=location)

# Re-export for backwards compatibility (deploy.py, tests, etc.)
PLANNER_MODEL = MODEL
MARATHON_PLANNER_INSTRUCTION = INSTRUCTION

from google.genai.types import GenerateContentConfig, ThinkingConfig

# Build agent kwargs — only set output_schema if defined
agent_kwargs = dict(
    name=AGENT_NAME,
    model=MODEL,
    description=AGENT_DESCRIPTION,
    static_instruction=INSTRUCTION,
    tools=get_tools(),
    generate_content_config=GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_budget=2048),
    ),
    after_agent_callback=auto_save_memories,
)

if OUTPUT_SCHEMA is not None:
    agent_kwargs["output_schema"] = OUTPUT_SCHEMA

root_agent = LlmAgent(**agent_kwargs)
