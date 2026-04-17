"""Memory Manager for Evaluator Agent.

Manages Memory Bank integration with custom topics for evaluation history.
Enables cross-session learning for scoring patterns and improvement tracking.
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


EVALUATION_HISTORY = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="evaluation_history",
        description="""Track evaluation results for marathon plans.

        Extract:
        - Overall scores and pass/fail verdicts
        - Which criteria had findings
        - Number of iterations to reach passing score
        - Plans that passed vs failed

        Format: "Evaluation: passed={verdict}, score={score}, findings={count}, iterations={n}"
        Example: "Evaluation: passed=true, score=0.91, findings=1, iterations=3"
        """,
    )
)

SCORING_TRENDS = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="scoring_trends",
        description="""Track scoring patterns across evaluations.

        Extract:
        - Which criteria consistently score low
        - Score improvements across iterations
        - Criteria that are hardest to satisfy
        - Average scores by category

        Format: "Trend: {criterion} avg_score={score}, common_issue={issue}"
        Example: "Trend: logistics_completeness avg_score=0.62, common_issue=missing water station details"
        """,
    )
)

IMPROVEMENT_PATTERNS = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="improvement_patterns",
        description="""Track which improvement suggestions were effective.

        Extract:
        - Suggestions given and whether they led to score improvement
        - Before/after scores when suggestions were followed
        - Common fixes that resolve specific findings
        - Suggestions that don't help

        Format: "Improvement: {suggestion} -> score_change={delta}"
        Example: "Improvement: 'Add water stations every 1.5 miles' -> logistics_completeness +0.25"
        """,
    )
)

CRITERIA_CALIBRATION = MemoryTopic(
    custom_memory_topic=CustomMemoryTopic(
        label="criteria_calibration",
        description="""Track calibration notes for evaluation criteria.

        Extract:
        - Cases where criteria were too strict or too lenient
        - Edge cases that need special handling
        - Metric scores that didn't match expected quality
        - Adjustments needed for specific city/event types

        Format: "Calibration: {criterion} note={note}"
        Example: "Calibration: financial_viability note=charity events should weight revenue lower"
        """,
    )
)


def create_evaluator_memory_topics() -> MemoryBankCustomizationConfig:
    """Create Memory Bank customization config with evaluator-specific topics.

    Returns:
        MemoryBankCustomizationConfig with 4 custom topics.
    """
    return MemoryBankCustomizationConfig(
        memory_topics=[
            EVALUATION_HISTORY,
            SCORING_TRENDS,
            IMPROVEMENT_PATTERNS,
            CRITERIA_CALIBRATION,
        ]
    )


def create_memory_service(
    project: str | None = None,
    location: str | None = None,
    agent_engine_id: str | None = None,
) -> VertexAiMemoryBankService | None:
    """Create a VertexAiMemoryBankService."""
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
