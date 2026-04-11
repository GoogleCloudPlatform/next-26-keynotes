"""Memory Manager for Marathon Planner Agent.

Manages Memory Bank integration with custom topics.
Enables cross-session learning.
"""

import os
from typing import TYPE_CHECKING

from google.adk.memory import VertexAiMemoryBankService
from vertexai._genai.types import (
    MemoryBankCustomizationConfig,
    MemoryBankCustomizationConfigMemoryTopic as MemoryTopic,
    MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic as CustomMemoryTopic,
)

if TYPE_CHECKING:
    from google.adk.agents.callback_context import CallbackContext


# ============================================================================
# CUSTOM MEMORY TOPICS
# ============================================================================

PLANNING_HISTORY = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="planning_history",
        description="""Track marathon plans generated across sessions.

        Extract:
        - City and date of planned marathon
        - Key route decisions and waypoints
        - Final plan score and iteration count
        - What feedback led to plan improvements

        Format: "Plan: city={city}, date={date}, score={score}, iterations={n}"
        Example: "Plan: city=Las Vegas, date=2026-10-15, score=92, iterations=3"
        """,
    )
)

USER_PREFERENCES = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="user_preferences",
        description="""Track user preferences and constraints across sessions.

        Extract:
        - Preferred marathon themes (scenic, fast, charity)
        - Budget priorities (maximize revenue, minimize cost)
        - Scale preferences (participant count ranges)
        - City preferences and past cities planned

        Format: "Preference: type={type}, value={value}"
        Example: "Preference: type=theme, value=scenic"
        """,
    )
)

ROUTE_PATTERNS = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="route_patterns",
        description="""Track successful route patterns and lessons learned.

        Extract:
        - Route segments that received positive feedback
        - Waypoint combinations that hit the 26.2-mile target
        - Landmarks that enhance runner experience
        - Route decisions that caused issues

        Format: "Route: city={city}, pattern={pattern}, outcome={outcome}"
        Example: "Route: city=Las Vegas, pattern=Strip-to-Fremont loop, outcome=positive"
        """,
    )
)

LOGISTICS_INSIGHTS = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="logistics_insights",
        description="""Track logistics decisions and capacity learnings.

        Extract:
        - Water station placement strategies
        - Start/finish venue capacity findings
        - Crowd management approaches that worked
        - Budget estimates and actual costs

        Format: "Logistics: category={cat}, insight={insight}"
        Example: "Logistics: category=water_stations, insight=every 1.5 miles for 30k+ events"
        """,
    )
)


def create_marathon_planner_memory_topics() -> MemoryBankCustomizationConfig:
    """Create Memory Bank customization config with custom topics.

    Returns:
        MemoryBankCustomizationConfig with custom topics.
    """
    return MemoryBankCustomizationConfig(
        memory_topics=[
            PLANNING_HISTORY,
            USER_PREFERENCES,
            ROUTE_PATTERNS,
            LOGISTICS_INSIGHTS,
        ]
    )


# ============================================================================
# MEMORY SERVICE
# ============================================================================


def create_memory_service(
    project: str | None = None,
    location: str | None = None,
    agent_engine_id: str | None = None,
) -> VertexAiMemoryBankService | None:
    """Create a VertexAiMemoryBankService.

    Args:
        project: Google Cloud project ID. Defaults to GOOGLE_CLOUD_PROJECT env var.
        location: Google Cloud location. Defaults to GOOGLE_CLOUD_LOCATION env var.
        agent_engine_id: Agent Engine ID. Defaults to AGENT_ENGINE_ID env var.

    Returns:
        VertexAiMemoryBankService instance, or None if agent_engine_id is not set.
    """
    project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = location or (
        os.environ.get("AGENT_ENGINE_LOCATION")
        or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    agent_engine_id = agent_engine_id or os.environ.get("AGENT_ENGINE_ID")

    if not project:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable required")

    if not agent_engine_id:
        return None

    return VertexAiMemoryBankService(
        project=project,
        location=location,
        agent_engine_id=agent_engine_id,
    )


async def auto_save_memories(callback_context: "CallbackContext") -> None:
    """Automatically save session to Memory Bank after agent responds.

    Args:
        callback_context: ADK callback context with session information
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = (
        os.environ.get("AGENT_ENGINE_LOCATION")
        or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    agent_engine_id = os.environ.get("AGENT_ENGINE_ID")

    if not agent_engine_id:
        return

    try:
        memory_service = VertexAiMemoryBankService(
            project=project_id,
            location=location,
            agent_engine_id=agent_engine_id,
        )

        await memory_service.add_session_to_memory(
            callback_context._invocation_context.session
        )

    except Exception as e:
        print(f"Warning: Failed to save memories: {e}")
