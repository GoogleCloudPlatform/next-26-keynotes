"""Evaluator Agent - LLM-as-Judge for marathon plan quality evaluation.

Modules:
    agent: Core LlmAgent with ADK Skills and structured EvaluationResult output
    skills: ADK Skill definitions (evaluate-plan-quality, interpret-evaluation-scores, suggest-plan-improvements)
    runtime: A2A integration, deployment, and local testing
    services: Memory Bank and session management
"""

try:
    from .agent import root_agent, AGENT_NAME, MODEL

    __all__ = ["root_agent", "AGENT_NAME", "MODEL"]
except Exception:
    root_agent = None
    __all__ = ["root_agent"]
