"""Pydantic schemas for ADK structured outputs.

Re-exports from per-agent schema modules. Each agent owns its schemas locally
to simplify Agent Engine deployment (no cross-package imports needed).

For local development and tests, import from here:
    from src.schemas import EvaluationResult, MarathonPlan, ...

For agent code, import from the local module:
    from .schemas import MarathonPlan
"""

# Evaluator Agent schemas (internal to Planner)
from .planner_agent.evaluator.schemas import EvaluationResult, EvaluationFinding

# Marathon Planner Agent schemas
from .planner_agent.core.schemas import MarathonPlan

# Simulation Controller Agent schemas
from .simulator_agent.core.schemas import SimulationApproval

__all__ = [
    # Evaluator
    "EvaluationResult",
    "EvaluationFinding",
    # Marathon Planner
    "MarathonPlan",
    # Simulation Controller
    "SimulationApproval",
]
