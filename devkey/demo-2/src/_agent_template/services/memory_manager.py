"""Memory Manager for the {{AGENT_DISPLAY_NAME}}.

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
# CUSTOM MEMORY TOPICS (scenario-specific — edit these when scenario changes)
# ============================================================================

# TODO: Define your custom memory topics. Each topic tells the Memory Bank
# what information to extract and remember from conversations.
# Good topics are specific and include format examples.
# Typically 3-5 topics per agent.

TOPIC_1 = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="topic_1",
        description="""TODO: Describe what to extract and remember.

        Extract:
        - Key data point 1
        - Key data point 2

        Format: "Topic1: key={value}"
        Example: "Topic1: key=example_value"
        """,
    )
)

TOPIC_2 = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="topic_2",
        description="""TODO: Describe what to extract and remember.

        Extract:
        - Key data point 1
        - Key data point 2

        Format: "Topic2: key={value}"
        Example: "Topic2: key=example_value"
        """,
    )
)


def {{MEMORY_FUNC}}() -> MemoryBankCustomizationConfig:
    """Create Memory Bank customization config with custom topics.

    Returns:
        MemoryBankCustomizationConfig with custom topics.
    """
    return MemoryBankCustomizationConfig(
        memory_topics=[
            TOPIC_1,
            TOPIC_2,
            # TODO: Add more topics as needed
        ]
    )


# ============================================================================
# SCAFFOLDING (same across all agents — do not edit per scenario)
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
    """Automatically save session to Memory Bank after agent responds.

    This callback is triggered after each agent response to persist
    insights to Memory Bank. Memory extraction is asynchronous.
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
