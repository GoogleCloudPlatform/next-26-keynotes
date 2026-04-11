"""Marathon Planner Agent — Lead Orchestrator for city marathons.

Phase 1: Designs marathon plans with text output
Phase 2: Evaluates plans using Evaluator agent
Phase 3: Coordinates Evaluator and Simulation Controller via A2A.

Modules:
    agent: Core LlmAgent with ADK Skills and tools
    skills: ADK Skill definitions (design-marathon-route, coordinate-specialist-agents, iterate-evaluation-loop)
    runtime: A2A integration, Cloud Run deployment, and local testing
    services: Memory Bank and session management
"""

try:
    from .core import root_agent
    from .core.agent import PLANNER_MODEL
    from .core.config import AGENT_NAME, MODEL

    from .runtime.agent_card import create_marathon_planner_card
    from .runtime.agent_executor import MarathonPlannerExecutor

    from .services.memory_manager import (
        auto_save_memories,
        create_marathon_planner_memory_topics,
        create_memory_service,
    )
    from .services.session_manager import (
        SessionManager,
        TTLCache,
        create_session_service,
    )

    __all__ = [
        # Agent
        "root_agent",
        "AGENT_NAME",
        "MODEL",
        "PLANNER_MODEL",
        # A2A
        "create_marathon_planner_card",
        "MarathonPlannerExecutor",
        # Memory
        "create_marathon_planner_memory_topics",
        "create_memory_service",
        "auto_save_memories",
        # Session
        "SessionManager",
        "TTLCache",
        "create_session_service",
    ]
except Exception:
    root_agent = None
    __all__ = ["root_agent"]
