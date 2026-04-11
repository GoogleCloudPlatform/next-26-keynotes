"""Simulation Controller Agent - Reviews marathon plans for simulation readiness.

Wires config + skills + tools into the LlmAgent.
"""

import os
import pathlib

import vertexai
from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.skill_toolset import SkillToolset

from ..services.memory_manager import auto_save_memories
from .config import AGENT_DESCRIPTION, AGENT_NAME, MODEL, OUTPUT_SCHEMA
from .prompts import INSTRUCTION
from .tools import get_tools

# Initialize Vertex AI - required for LLM access
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
if project_id:
    vertexai.init(project=project_id, location=location)

# Load skills from the skills/ directory
_skills_dir = pathlib.Path(__file__).parent.parent / "skills"
_review_skill = load_skill_from_dir(_skills_dir / "review-marathon-plan")

_skill_toolset = SkillToolset(skills=[_review_skill])

# Build tools list: SkillToolset + PreloadMemoryTool + FunctionTools
_tools = [
    _skill_toolset,
    PreloadMemoryTool(),
    *get_tools(),
]

from google.genai.types import GenerateContentConfig, ThinkingConfig

# Build agent kwargs, only adding output_schema if it is set
_agent_kwargs = dict(
    name=AGENT_NAME,
    model=MODEL,
    description=AGENT_DESCRIPTION,
    static_instruction=INSTRUCTION,
    tools=_tools,
    generate_content_config=GenerateContentConfig(
        thinking_config=ThinkingConfig(thinking_budget=0),
        max_output_tokens=4096,
    ),
    after_agent_callback=auto_save_memories,
)
if OUTPUT_SCHEMA is not None:
    _agent_kwargs["output_schema"] = OUTPUT_SCHEMA

root_agent = LlmAgent(**_agent_kwargs)
