"""Schemas for the Simulation Controller Agent.

Defines structured output formats used by this agent.
Kept local to simplify Agent Engine deployment (no cross-package imports).
"""

from pydantic import BaseModel, Field


class SimulationApproval(BaseModel):
    """Structured output from the Simulation Controller Agent."""

    approved: bool = Field(
        description="Whether the plan is approved for simulation execution",
    )
    overall_readiness: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall readiness score (0.0 to 1.0)",
    )
    route_feasibility: str = Field(
        description="Assessment of route feasibility: 'feasible', 'marginal', or 'infeasible'",
    )
    logistics_readiness: str = Field(
        description="Assessment of logistics readiness: 'ready', 'partial', or 'not_ready'",
    )
    safety_clearance: str = Field(
        description="Safety clearance status: 'cleared', 'conditional', or 'blocked'",
    )
    blockers: list[str] = Field(
        default_factory=list,
        description="List of blocking issues that must be resolved before approval",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Non-blocking recommendations for plan improvement",
    )
    summary: str = Field(
        default="",
        description="Brief natural-language summary of the approval decision",
    )
