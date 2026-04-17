"""A2A Agent Card for Simulation Controller Agent.

Describes the agent's capabilities for A2A protocol discovery.
Uses vertexai utility for proper Agent Engine integration.
"""

from a2a.types import AgentCard, AgentSkill
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card


def create_simulation_controller_card() -> AgentCard:
    """Create an A2A AgentCard for Simulation Controller Agent.

    Returns:
        AgentCard describing the agent's capabilities
    """
    review_marathon_skill = AgentSkill(
        id="review_marathon_plan",
        name="Review Marathon Plan",
        description=(
            "Review a marathon plan for simulation readiness. Assesses route "
            "feasibility, logistics completeness, and safety clearance. "
            "Returns a structured SimulationApproval with approval decision,"
            "blockers, and recommendations."
        ),
        tags=["simulation", "review", "approval", "marathon"],
        examples=[
            "Review this marathon plan for simulation readiness",
            "Is this plan ready for simulation execution?",
            "Approve or reject this marathon plan for simulation",
        ],
    )

    return create_agent_card(
        agent_name="simulator_agent",
        description=(
            "Simulation Controller Agent - Reviews marathon plans for simulation "
            "readiness. Assesses route feasibility, logistics completeness, and "
            "safety clearance. Returns structured SimulationApproval."
        ),
        skills=[review_marathon_skill],
    )
