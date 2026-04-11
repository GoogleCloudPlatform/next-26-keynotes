"""TDD for Planner Workflow Optimization.

Verifies:
1. Single-pass evaluation (only one call to evaluator).
2. "Pre-flight" logic (implicit, by checking instruction influence).
"""

import json
import os
import pytest
import uuid
from unittest.mock import AsyncMock, patch
from src.planner_agent.core.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("GOOGLE_CLOUD_PROJECT"),
    reason="Requires GOOGLE_CLOUD_PROJECT for live Gemini API",
)
async def test_planner_calls_evaluator_only_once():
    """RED: Test that the planner calls the evaluator exactly once (Integration)."""
    
    # Initialize runner for local test
    runner = Runner(
        app_name="planner_app",
        agent=root_agent,
        session_service=InMemorySessionService(),
        auto_create_session=True
    )

    # We patch the run_async method of the evaluator agent tool
    # Note: the Evaluator is a local AgentTool, so we patch its internal agent's run_async_impl
    # We patch AgentTool.run_async which is what the Planner uses to call the Evaluator
    from google.adk.tools.agent_tool import AgentTool
    
    original_run = AgentTool.run_async
    
    mock_eval_call_count = 0

    async def mock_tool_run(self, *args, **kwargs):
        nonlocal mock_eval_call_count
        agent_name = getattr(self.agent, "name", "")
        print(f"\n[DEBUG] Tool called: {agent_name}")
        if agent_name == "evaluator_agent":
            mock_eval_call_count += 1
            return {
                "passed": False,
                "overall_score": 0.7,
                "findings": [{"criterion": "safety_compliance", "severity": "medium", "description": "Needs more water"}],
                "improvement_suggestions": ["Add more water stations"]
            }
        return await original_run(self, *args, **kwargs)

    with patch.object(AgentTool, "run_async", autospec=True, side_effect=mock_tool_run):
        # Trigger the planner with a very explicit request
        query = "Generate a marathon plan for Chicago and then evaluate it using the evaluator_agent. You MUST call the evaluator."
        user_msg = types.Content(parts=[types.Part(text=query)], role="user")
        
        print("\n[DEBUG] Starting planner...")
        async for event in runner.run_async(
            user_id="test_user",
            session_id=str(uuid.uuid4()),
            new_message=user_msg
        ):
            if event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"Agent: {part.text[:50]}...")
                    if part.function_call:
                        print(f"Tool Call: {part.function_call.name}")
        
        print(f"\n[DEBUG] Final call count: {mock_eval_call_count}")
        # In the RED state, the planner will likely try to call the evaluator twice 
        # (initial + revision) because the prompt says "Iterate exactly once".
        # We want to change this to 1 in Cycle 3 GREEN.
        assert mock_eval_call_count == 1
