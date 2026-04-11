"""Configuration for the Marathon Planner Agent.

Agent identity, model, and output schema.
Prompt lives in prompts.py.
"""

import os

# Agent identity
AGENT_NAME = "planner_agent"
AGENT_DESCRIPTION = (
    "Marathon Planner Agent — Lead Architect. "
    "Designs comprehensive city marathon plans with built-in expertise in route design, "
    "traffic management, community impact, and economics. Evaluates plans via the "
    "Evaluator Agent (A2A) and submits for approval to the Simulation Controller (A2A). "
    "Produces detailed marathon plans with structured evaluation."
)

# Model configuration
MODEL = os.getenv("PLANNER_MODEL", "gemini-3-flash-preview")

# Phase 1: No structured output — agent returns free-form text
# Phase 2+: Set to MarathonPlan for structured output
OUTPUT_SCHEMA = None
