"""Tests for the Marathon Planner Agent (Cloud Run Orchestrator).

Tests the deployed agent via A2A protocol on Cloud Run.
Local tests have been consolidated into test_planner_agent.py.

Usage:
    # Run all tests (local only)
    uv run pytest tests/test_orchestrator_agent.py -v

    # Run with Cloud Run tests
    ORCHESTRATOR_URL=https://orchestrator-agent-xxx.a.run.app \
    uv run pytest tests/test_orchestrator_agent.py -v
"""

import asyncio
import json
import os
import subprocess
import uuid

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Default Cloud Run URL
CLOUD_RUN_URL = os.environ.get(
    "ORCHESTRATOR_URL",
    ""
)


def get_auth_token() -> str | None:
    """Get Google Cloud identity token for authenticated requests."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


class TestMarathonPlannerLocal:
    """Test Marathon Planner agent creation locally (quick smoke tests)."""

    def test_agent_module_imports(self):
        """Test that agent module can be imported."""
        from src.planner_agent import (
            root_agent,
            AGENT_NAME,
            PLANNER_MODEL,
            create_marathon_planner_card,
            MarathonPlannerExecutor,
        )

        assert root_agent is not None
        assert AGENT_NAME == "planner_agent"
        assert PLANNER_MODEL is not None

    def test_agent_name_constant(self):
        """Test agent name constant is correct."""
        from src.planner_agent import AGENT_NAME

        assert AGENT_NAME == "planner_agent"

    def test_agent_model_is_gemini(self):
        """Test agent uses Gemini model."""
        from src.planner_agent import PLANNER_MODEL

        assert "gemini" in PLANNER_MODEL.lower()

    def test_root_agent_exists(self):
        """Test root_agent is created."""
        from src.planner_agent import root_agent

        assert root_agent is not None
        assert root_agent.name == "planner_agent"

    def test_agent_has_tools(self):
        """Test agent has tools configured."""
        from src.planner_agent import root_agent

        assert root_agent.tools is not None
        # SkillToolset + PreloadMemoryTool + evaluate_my_plan
        assert len(root_agent.tools) >= 3

    def test_agent_card_name(self):
        """Test agent card has correct name."""
        from src.planner_agent import create_marathon_planner_card

        agent_card = create_marathon_planner_card()
        assert agent_card.name == "planner_agent"

    def test_agent_card_has_streaming(self):
        """Test agent card advertises streaming capability."""
        from src.planner_agent import create_marathon_planner_card

        agent_card = create_marathon_planner_card()
        assert agent_card.capabilities is not None
        assert agent_card.capabilities.streaming is True

    def test_agent_card_has_skills(self):
        """Test agent card has skills defined."""
        from src.planner_agent import create_marathon_planner_card

        agent_card = create_marathon_planner_card()
        assert agent_card.skills is not None
        assert len(agent_card.skills) > 0

    def test_agent_card_marathon_skill(self):
        """Test agent card has marathon planning skill."""
        from src.planner_agent import create_marathon_planner_card

        agent_card = create_marathon_planner_card()
        skill_ids = [s.id for s in agent_card.skills]
        assert "plan_marathon" in skill_ids

    def test_agent_card_serializes_to_json(self):
        """Test agent card can be serialized to JSON."""
        from src.planner_agent import create_marathon_planner_card

        agent_card = create_marathon_planner_card()
        card_dict = agent_card.model_dump()
        json_str = json.dumps(card_dict)

        assert len(json_str) > 0
        assert "planner_agent" in json_str


class TestMarathonPlannerExecutor:
    """Test Marathon Planner executor creation."""

    def test_executor_class_exists(self):
        """Test executor class can be imported."""
        from src.planner_agent import MarathonPlannerExecutor

        assert MarathonPlannerExecutor is not None

    def test_executor_can_be_instantiated(self):
        """Test executor can be created."""
        from src.planner_agent import MarathonPlannerExecutor

        executor = MarathonPlannerExecutor()
        assert executor is not None


class TestMarathonPlannerTools:
    """Test Marathon Planner tools."""

    def test_tools_module_imports(self):
        """Test tools module can be imported."""
        from src.planner_agent.core import tools

        assert tools is not None

    def test_get_tools_returns_list(self):
        """Test get_tools returns a list."""
        from src.planner_agent.core.tools import get_tools

        tools = get_tools()
        assert isinstance(tools, list)
        # SkillToolset + PreloadMemoryTool (+ A2A tools if env vars set)
        assert len(tools) >= 2

    def test_a2a_agent_creators_exist(self):
        """Test A2A agent creation functions are accessible."""
        from src.planner_agent.core import tools

        assert hasattr(tools, "create_evaluator_tool")
        assert hasattr(tools, "create_simulation_controller_tool")


class TestMarathonPlannerDeployed:
    """Test deployed Marathon Planner via A2A protocol.

    These tests require a deployed agent and network access.
    Set ORCHESTRATOR_URL environment variable to run.
    """

    @pytest.fixture
    def auth_token(self):
        """Get authentication token for Cloud Run."""
        return get_auth_token()

    @pytest.fixture
    def base_url(self):
        """Get the deployed agent URL."""
        return CLOUD_RUN_URL.rstrip("/")

    @pytest.mark.skipif(
        not os.environ.get("ORCHESTRATOR_URL"),
        reason="ORCHESTRATOR_URL not set",
    )
    @pytest.mark.asyncio
    async def test_deployed_agent_card(self, base_url, auth_token):
        """Test fetching agent card from deployed service."""
        import httpx

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/.well-known/agent.json",
                headers=headers,
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            agent_card = response.json()
            assert agent_card.get("name") == "planner_agent"
            assert "capabilities" in agent_card

    @pytest.mark.skipif(
        not os.environ.get("ORCHESTRATOR_URL"),
        reason="ORCHESTRATOR_URL not set",
    )
    @pytest.mark.asyncio
    async def test_deployed_simple_request(self, base_url, auth_token):
        """Test sending a simple request to deployed service."""
        import httpx

        message_id = str(uuid.uuid4())

        request_data = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "id": message_id,
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"kind": "text", "text": "What can you help me plan?"}],
                }
            },
        }

        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                base_url,
                json=request_data,
                headers=headers,
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            result = response.json()
            assert "result" in result or "error" in result


async def run_quick_test():
    """Quick test function to verify deployed agent.

    Run with: uv run python -m tests.test_orchestrator_agent
    """
    print("=" * 60)
    print("Marathon Planner Agent - Quick Test")
    print("=" * 60)
    print()

    print("Local Tests:")
    print("-" * 60)

    try:
        from src.planner_agent import (
            root_agent,
            AGENT_NAME,
            PLANNER_MODEL,
        )

        print(f"  Agent name: {root_agent.name}")
        print(f"  Model: {PLANNER_MODEL}")
        print(f"  Tools count: {len(root_agent.tools) if root_agent.tools else 0}")
        print("  Local tests passed!")
    except Exception as e:
        print(f"  Error: {e}")
        return

    print()
    print("=" * 60)
    print("Quick test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_quick_test())
