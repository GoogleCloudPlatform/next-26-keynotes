"""Simulation Controller Agent - Approves or rejects marathon plans for simulation.

Modules:
    agent/: Agent definition (config, prompts, schemas, LlmAgent wiring)
    skills/: ADK Skills (procedural knowledge + references + scripts)
    runtime/: Deployment & serving (agent card, executor, deploy, local server)
    services/: Memory Bank and session management
"""

try:
    from .core import root_agent
    from .core.config import AGENT_NAME, MODEL

    __all__ = ["root_agent", "AGENT_NAME", "MODEL"]
except Exception:
    pass
