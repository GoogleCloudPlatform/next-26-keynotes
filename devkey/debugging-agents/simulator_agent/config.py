"""Configuration for the Simulation Controller Agent.

Agent identity, model, and schema. Prompt lives in prompts.py.
"""

import os

from .schemas import SimulationApproval

# Agent identity
AGENT_NAME = "simulator_agent"
AGENT_DESCRIPTION = (
    "Simulation Controller Agent. "
    "Reviews marathon plans for simulation readiness, assessing route feasibility, "
    "logistics completeness, and safety clearance. Returns a structured approval "
    "decision with blockers and recommendations."
)

# Model configuration
MODEL = os.getenv("SIMULATOR_MODEL", "gemini-3-flash-preview")

# Structured output schema
OUTPUT_SCHEMA = SimulationApproval
