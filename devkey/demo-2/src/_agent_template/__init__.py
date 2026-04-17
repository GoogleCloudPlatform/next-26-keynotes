"""{{AGENT_DISPLAY_NAME}} - TODO: Add one-line description.

Modules:
    agent/: Agent definition (config, prompts, schemas, LlmAgent wiring)
    skills/: ADK Skills (procedural knowledge + references + scripts)
    runtime/: Deployment & serving (agent card, executor, deploy, local server)
    services/: Memory Bank and session management
"""

# Lazy imports: on Agent Engine, module-level agent construction may fail
# because the environment isn't fully configured during unpickling.
# The executor uses lazy initialization (_init_agent) instead.
try:
    from .core import root_agent
    from .core.config import AGENT_NAME, MODEL

    __all__ = ["root_agent", "AGENT_NAME", "MODEL"]
except Exception:
    pass
