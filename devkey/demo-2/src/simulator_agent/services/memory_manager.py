"""Memory Manager for Simulation Controller Agent.

Manages Memory Bank integration with custom topics for simulation review history.
Enables cross-session learning for approval patterns and readiness tracking.
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


APPROVAL_HISTORY = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="approval_history",
        description="""Track approval decisions for marathon plans.

        Extract:
        - Approval verdicts (approved, conditional, rejected)
        - Overall readiness scores
        - Common blockers and their resolution
        - Number of review iterations before approval

        Format: "Approval: approved={verdict}, readiness={score}, blockers={count}"
        Example: "Approval: approved=true, readiness=0.92, blockers=0"
        """,
    )
)

READINESS_PATTERNS = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="readiness_patterns",
        description="""Track readiness patterns across plan reviews.

        Extract:
        - Which readiness dimensions consistently fail
        - Common missing elements in plans
        - Improvement patterns across review iterations

        Format: "Pattern: {dimension} avg_readiness={score}, common_gap={issue}"
        Example: "Pattern: logistics_readiness avg_readiness=0.65, common_gap=insufficient water stations"
        """,
    )
)


def create_simulation_controller_memory_topics() -> MemoryBankCustomizationConfig:
    """Create Memory Bank customization config with custom topics.

    Returns:
        MemoryBankCustomizationConfig with custom topics.
    """
    return MemoryBankCustomizationConfig(
        memory_topics=[
            APPROVAL_HISTORY,
            READINESS_PATTERNS,
        ]
    )


# ============================================================================
# SCAFFOLDING (same across all agents -- do not edit per scenario)
# ============================================================================


def create_memory_service(
    project: str | None = None,
    location: str | None = None,
    agent_engine_id: str | None = None,
) -> VertexAiMemoryBankService | None:
    """Create a VertexAiMemoryBankService.

    Returns None if agent_engine_id is not set (local development).
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
    """Automatically save session to Memory Bank after agent responds."""
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
