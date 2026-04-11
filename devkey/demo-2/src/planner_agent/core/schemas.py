"""Schemas for the Marathon Planner Agent.

Defines structured output formats used by this agent.
Kept local to simplify Agent Engine deployment (no cross-package imports).

Phase 1: No structured output (text-only). Schemas defined here for
future phases when structured output is needed.
"""

from pydantic import BaseModel, Field


class MarathonPlan(BaseModel):
    """Structured marathon plan output (used in Phase 2+)."""

    city: str = Field(description="City where the marathon takes place")
    date: str = Field(description="Event date in YYYY-MM-DD format")
    theme: str = Field(description="Marathon theme: scenic, fast, charity, etc.")
    participants: int = Field(ge=0, description="Expected number of participants")
    route_summary: str = Field(description="High-level route description")
    route_waypoints: list[str] = Field(
        default_factory=list, description="Ordered list of route waypoints"
    )
    distance_miles: float = Field(
        ge=0, description="Total route distance in miles"
    )
    logistics_summary: str = Field(description="Key logistics: water stations, start/finish, timing")
    budget_summary: str = Field(description="Budget overview: costs, revenue projections, sponsors")
    key_risks: list[str] = Field(
        default_factory=list, description="Top risks and mitigation strategies"
    )
