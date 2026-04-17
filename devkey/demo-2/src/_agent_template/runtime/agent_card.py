"""A2A Agent Card for the {{AGENT_DISPLAY_NAME}}.

Describes the agent's capabilities for A2A protocol discovery.
"""

from a2a.types import AgentCard, AgentCapabilities, AgentSkill


def {{CARD_FUNC}}(
    base_url: str = "http://localhost:{{PORT}}",
) -> AgentCard:
    """Create an A2A AgentCard for the {{AGENT_DISPLAY_NAME}}.

    Args:
        base_url: The agent's base URL for A2A protocol.

    Returns:
        AgentCard describing the agent's capabilities.
    """
    return AgentCard(
        name="{{AGENT_MODULE}}",
        description=(
            # TODO: Write the agent card description
            "{{AGENT_DISPLAY_NAME}} - Describe capabilities for A2A discovery."
        ),
        url=base_url,
        version="1.0.0",
        default_input_modes=["text", "text/plain"],
        default_output_modes=["text", "text/plain", "application/json"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[
            AgentSkill(
                id="todo_skill_id",  # TODO: Unique skill identifier
                name="TODO Skill Name",  # TODO: Human-readable skill name
                description=(
                    # TODO: Describe what this skill does
                    "Describe the agent's primary capability."
                ),
                tags=["todo"],  # TODO: Add relevant tags
                examples=[
                    # TODO: Add example queries that trigger this skill
                    "Example query 1",
                    "Example query 2",
                ],
            ),
        ],
    )
