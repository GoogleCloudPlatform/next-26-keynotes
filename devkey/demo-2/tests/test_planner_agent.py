"""Tests for the Marathon Planner Agent.

Tests agent creation, configuration, ADK Skills, tools, agent card,
executor, memory, session, schemas, and module structure.

Usage:
    uv run pytest tests/test_planner_agent.py -v
"""

import json
import os
import pathlib

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Agent module root
AGENT_ROOT = pathlib.Path(__file__).parent.parent / "src" / "planner_agent"


class TestMarathonPlannerSchemas:
    """Test Marathon Planner schemas."""

    def test_marathon_plan_schema_fields(self):
        """Test MarathonPlan schema has required fields."""
        from src.planner_agent.core.schemas import MarathonPlan

        fields = MarathonPlan.model_fields
        assert "city" in fields
        assert "date" in fields
        assert "theme" in fields
        assert "participants" in fields
        assert "route_summary" in fields
        assert "distance_miles" in fields
        assert "logistics_summary" in fields
        assert "budget_summary" in fields
        assert "key_risks" in fields
        assert "route_waypoints" in fields

    def test_marathon_plan_creation(self):
        """Test MarathonPlan can be created and serialized."""
        from src.planner_agent.core.schemas import MarathonPlan

        plan = MarathonPlan(
            city="Las Vegas",
            date="2026-10-15",
            theme="scenic",
            participants=30000,
            route_summary="Strip to Fremont loop",
            route_waypoints=["Mandalay Bay", "Bellagio", "Fremont Street"],
            distance_miles=26.2,
            logistics_summary="22 water stations, 5 medical tents",
            budget_summary="$2M budget, $3M projected revenue",
            key_risks=["Heat in October", "Strip traffic disruption"],
        )

        data = plan.model_dump()
        assert data["city"] == "Las Vegas"
        assert data["distance_miles"] == 26.2
        assert len(data["route_waypoints"]) == 3

        json_str = json.dumps(data)
        assert len(json_str) > 0

    def test_schemas_importable_from_top_level(self):
        """Test schemas can be imported via src.schemas."""
        from src.schemas import MarathonPlan
        from src.planner_agent.core.schemas import MarathonPlan as Direct

        assert MarathonPlan is Direct


class TestMarathonPlannerConfig:
    """Test Marathon Planner configuration."""

    def test_agent_name(self):
        """Test agent name is correct."""
        from src.planner_agent.core.config import AGENT_NAME

        assert AGENT_NAME == "planner_agent"

    def test_model_default(self):
        """Test agent uses Gemini model."""
        from src.planner_agent.core.config import MODEL

        assert "gemini" in MODEL.lower()

    def test_output_schema_is_none(self):
        """Test Phase 1 has no structured output schema."""
        from src.planner_agent.core.config import OUTPUT_SCHEMA

        assert OUTPUT_SCHEMA is None

    def test_description_is_nonempty(self):
        """Test description is set."""
        from src.planner_agent.core.config import AGENT_DESCRIPTION

        assert len(AGENT_DESCRIPTION) > 10
        assert "Architect" in AGENT_DESCRIPTION

    def test_instruction_is_nonempty(self):
        """Test instruction is set."""
        from src.planner_agent.core.prompts import INSTRUCTION

        assert len(INSTRUCTION) > 100

    def test_instruction_mentions_marathon(self):
        """Test instruction is marathon-focused."""
        from src.planner_agent.core.prompts import INSTRUCTION

        assert "marathon" in INSTRUCTION.lower()
        assert "26.2" in INSTRUCTION

    def test_instruction_mentions_skills(self):
        """Test instruction mentions ADK Skills."""
        from src.planner_agent.core.prompts import INSTRUCTION

        assert "route-planning" in INSTRUCTION
        assert "plan-evaluation" in INSTRUCTION

    def test_instruction_mentions_a2a_agents(self):
        """Test instruction mentions A2A agents."""
        from src.planner_agent.core.prompts import INSTRUCTION

        instruction_lower = INSTRUCTION.lower()
        assert "evaluator" in instruction_lower
        assert "simulator" in instruction_lower or "simulation controller" in instruction_lower

    def test_instruction_mentions_evaluation(self):
        """Test instruction mentions evaluation."""
        from src.planner_agent.core.prompts import INSTRUCTION

        assert "scoring" in INSTRUCTION.lower() or "evaluation" in INSTRUCTION.lower()


class TestMarathonPlannerSkills:
    """Test Marathon Planner ADK Skills."""

    def test_route_skill_loads(self):
        """Test route-planning skill loads."""
        from google.adk.skills import load_skill_from_dir

        skill = load_skill_from_dir(AGENT_ROOT / "skills" / "route-planning")
        assert skill is not None

    def test_all_consolidated_skills_load(self):
        """Test all consolidated skills load."""
        from google.adk.skills import load_skill_from_dir

        skills_dir = AGENT_ROOT / "skills"
        skill_dirs = sorted([
            d for d in skills_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ])
        assert len(skill_dirs) == 2
        for skill_dir in skill_dirs:
            skill = load_skill_from_dir(skill_dir)
            assert skill is not None, f"Failed to load skill: {skill_dir.name}"

    def test_evaluation_skill_loads(self):
        """Test plan-evaluation skill loads."""
        from google.adk.skills import load_skill_from_dir

        skill = load_skill_from_dir(AGENT_ROOT / "skills" / "plan-evaluation")
        assert skill is not None

    def test_route_skill_has_references(self):
        """Test route skill has reference files."""
        refs_dir = AGENT_ROOT / "skills" / "route-planning" / "references"
        assert refs_dir.is_dir()
        ref_files = list(refs_dir.glob("*.md"))
        assert len(ref_files) >= 1

    def test_all_skills_have_references(self):
        """Test all consolidated skills have reference files."""
        skills_dir = AGENT_ROOT / "skills"
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue
            refs_dir = skill_dir / "references"
            assert refs_dir.is_dir(), f"Missing references/ in {skill_dir.name}"
            ref_files = list(refs_dir.glob("*.md"))
            assert len(ref_files) >= 1, f"No .md files in {skill_dir.name}/references/"

    def test_evaluation_skill_has_references(self):
        """Test evaluation skill has reference files."""
        refs_dir = AGENT_ROOT / "skills" / "plan-evaluation" / "references"
        assert refs_dir.is_dir()
        ref_files = list(refs_dir.glob("*.md"))
        assert len(ref_files) >= 1

    def test_route_skill_has_scripts(self):
        """Test route skill has script files."""
        scripts_dir = AGENT_ROOT / "skills" / "route-planning" / "scripts"
        assert scripts_dir.is_dir()
        script_files = list(scripts_dir.glob("*.py"))
        assert len(script_files) >= 1

    def test_all_skills_have_scripts(self):
        """Test all consolidated skills have script files."""
        skills_dir = AGENT_ROOT / "skills"
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
                continue
            scripts_dir = skill_dir / "scripts"
            assert scripts_dir.is_dir(), f"Missing scripts/ in {skill_dir.name}"
            script_files = list(scripts_dir.glob("*.py"))
            assert len(script_files) >= 1, f"No .py files in {skill_dir.name}/scripts/"

    def test_evaluation_skill_has_scripts(self):
        """Test evaluation skill has script files."""
        scripts_dir = AGENT_ROOT / "skills" / "plan-evaluation" / "scripts"
        assert scripts_dir.is_dir()
        script_files = list(scripts_dir.glob("*.py"))
        assert len(script_files) >= 1

    def test_route_skill_resources_loaded(self):
        """Test route skill resources can be read."""
        from google.adk.skills import load_skill_from_dir

        skill = load_skill_from_dir(AGENT_ROOT / "skills" / "route-planning")
        assert skill.resources is not None

    def test_skill_toolset_creation(self):
        """Test SkillToolset can be created with skills."""
        from google.adk.skills import load_skill_from_dir
        from google.adk.tools.skill_toolset import SkillToolset

        skills_dir = AGENT_ROOT / "skills"
        skills = [
            load_skill_from_dir(d)
            for d in sorted(skills_dir.iterdir())
            if d.is_dir() and not d.name.startswith("_")
        ]
        assert len(skills) == 2
        toolset = SkillToolset(skills=skills)
        assert toolset is not None


class TestMarathonPlannerScripts:
    """Test Marathon Planner skill scripts."""

    def test_validate_route_script(self):
        """Test validate_route script."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_route",
            AGENT_ROOT / "skills" / "route-planning" / "scripts" / "validate_route.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        result = mod.validate_route(
            waypoints=["Start", "Mid1", "Mid2", "Mid3", "Mid4", "Mid5", "Mid6", "Mid7", "Finish"],
            distance_miles=26.2,
        )
        assert result["passed"] is True
        assert len(result["issues"]) == 0

    def test_validate_route_script_fails_short_distance(self):
        """Test validate_route catches short distance."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "validate_route",
            AGENT_ROOT / "skills" / "route-planning" / "scripts" / "validate_route.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        result = mod.validate_route(
            waypoints=["Start", "Finish"],
            distance_miles=10.0,
        )
        assert result["passed"] is False
        assert len(result["issues"]) > 0

    def test_check_evaluation_script(self):
        """Test check_evaluation script."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "check_evaluation",
            AGENT_ROOT / "skills" / "plan-evaluation" / "scripts" / "check_evaluation.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Test passed
        result = mod.check_evaluation(overall_score=0.92, passed=True, iteration=1)
        assert result["action"] == "present"

        # Test failed but can retry
        result = mod.check_evaluation(overall_score=0.70, passed=False, iteration=1)
        assert result["action"] == "revise"

        # Test max iterations reached
        result = mod.check_evaluation(overall_score=0.70, passed=False, iteration=3)
        assert result["action"] == "present_with_caveats"


class TestMarathonPlannerTools:
    """Test Marathon Planner tools."""

    def test_get_tools_returns_list(self):
        """Test get_tools returns a list."""
        from src.planner_agent.core.tools import get_tools

        tools = get_tools()
        assert isinstance(tools, list)
        # SkillToolset + PreloadMemoryTool + evaluate_my_plan = 3 minimum
        assert len(tools) >= 3

    def test_a2a_agent_creators_exist(self):
        """Test A2A agent creation functions are accessible."""
        from src.planner_agent.core import tools

        assert hasattr(tools, "create_evaluator_tool")
        assert hasattr(tools, "create_simulation_controller_tool")

    def test_serializable_remote_agent_class(self):
        """Test SerializableRemoteA2aAgent class exists."""
        from src.planner_agent.core.tools import SerializableRemoteA2aAgent

        assert SerializableRemoteA2aAgent is not None

    def test_a2a_url_helpers(self):
        """Test A2A URL helper functions."""
        from src.planner_agent.core.tools import (
            _get_agent_a2a_endpoint,
            _get_agent_a2a_url,
        )

        resource_name = "projects/123/locations/us-central1/reasoningEngines/456"

        endpoint = _get_agent_a2a_endpoint(resource_name)
        assert "us-central1-aiplatform.googleapis.com" in endpoint
        assert "/a2a/v1/card" in endpoint

        url = _get_agent_a2a_url(resource_name)
        assert "us-central1-aiplatform.googleapis.com" in url
        assert url.endswith("/a2a")

    def test_auth_module(self):
        """Test GoogleAuthRefresh class."""
        from src.planner_agent.core.auth import GoogleAuthRefresh

        auth = GoogleAuthRefresh()
        assert auth is not None
        assert auth.credentials is None  # Lazy init

    def test_evaluator_tool_is_local(self):
        """Test create_evaluator_tool returns a local AgentTool.

        This verifies the consolidation of Evaluator into Planner.
        """
        from google.adk.tools.agent_tool import AgentTool
        from google.adk.agents.llm_agent import LlmAgent
        from src.planner_agent.core.tools import create_evaluator_tool

        tool = create_evaluator_tool()
        assert isinstance(tool, AgentTool)
        assert isinstance(tool.agent, LlmAgent)
        assert tool.agent.name == "evaluator_agent"

    def test_evaluator_agent_no_longer_needs_resource_name(self):
        """Test create_evaluator_tool does not require environment variable."""
        from src.planner_agent.core.tools import create_evaluator_tool

        # Ensure env var is NOT set
        saved = os.environ.pop("EVALUATOR_AGENT_RESOURCE_NAME", None)
        try:
            # This should no longer raise ValueError
            tool = create_evaluator_tool()
            assert tool is not None
        finally:
            if saved:
                os.environ["EVALUATOR_AGENT_RESOURCE_NAME"] = saved

    def test_simulation_controller_creator_callable(self):
        """Test create_simulator_agent raises without env var."""
        from src.planner_agent.core.tools import create_simulator_agent

        saved = os.environ.pop("SIMULATOR_AGENT_RESOURCE_NAME", None)
        try:
            import pytest
            with pytest.raises(ValueError, match="SIMULATOR_AGENT_RESOURCE_NAME"):
                create_simulator_agent()
        finally:
            if saved:
                os.environ["SIMULATOR_AGENT_RESOURCE_NAME"] = saved


class TestMarathonPlannerAgent:
    """Test Marathon Planner agent creation."""

    def test_root_agent_importable(self):
        """Test root_agent can be imported."""
        from src.planner_agent import root_agent

        assert root_agent is not None

    def test_agent_name(self):
        """Test agent has correct name."""
        from src.planner_agent import root_agent

        assert root_agent.name == "planner_agent"

    def test_agent_has_skill_toolset(self):
        """Test agent has SkillToolset in tools."""
        from google.adk.tools.skill_toolset import SkillToolset
        from src.planner_agent import root_agent

        has_skill_toolset = any(
            isinstance(t, SkillToolset) for t in root_agent.tools
        )
        assert has_skill_toolset

    def test_agent_has_preload_memory_tool(self):
        """Test agent has PreloadMemoryTool."""
        from google.adk.tools.preload_memory_tool import PreloadMemoryTool
        from src.planner_agent import root_agent

        has_memory_tool = any(
            isinstance(t, PreloadMemoryTool) for t in root_agent.tools
        )
        assert has_memory_tool

    def test_agent_no_output_schema(self):
        """Test Phase 1 agent does not have structured output schema."""
        from src.planner_agent import root_agent

        output_schema = getattr(root_agent, "output_schema", None)
        assert output_schema is None

    def test_agent_importable_from_top_level(self):
        """Test backward-compatible imports from __init__.py."""
        from src.planner_agent import (
            root_agent,
            AGENT_NAME,
            PLANNER_MODEL,
            create_marathon_planner_card,
            MarathonPlannerExecutor,
        )

        assert root_agent is not None
        assert AGENT_NAME == "planner_agent"
        assert "gemini" in PLANNER_MODEL.lower()


class TestMarathonPlannerAgentCard:
    """Test Marathon Planner A2A agent card."""

    def test_agent_card_creation(self):
        """Test agent card can be created."""
        from src.planner_agent.runtime.agent_card import create_marathon_planner_card

        card = create_marathon_planner_card()
        assert card is not None
        assert card.name == "planner_agent"

    def test_agent_card_has_skills(self):
        """Test agent card has skills defined."""
        from src.planner_agent.runtime.agent_card import create_marathon_planner_card

        card = create_marathon_planner_card()
        assert card.skills is not None
        assert len(card.skills) > 0

    def test_agent_card_marathon_skill(self):
        """Test agent card has marathon planning skill."""
        from src.planner_agent.runtime.agent_card import create_marathon_planner_card

        card = create_marathon_planner_card()
        skill_ids = [s.id for s in card.skills]
        assert "plan_marathon" in skill_ids

    def test_agent_card_has_streaming(self):
        """Test agent card has streaming capability."""
        from src.planner_agent.runtime.agent_card import create_marathon_planner_card

        card = create_marathon_planner_card()
        assert card.capabilities is not None
        assert card.capabilities.streaming is True

    def test_agent_card_serializes_to_json(self):
        """Test agent card can be serialized to JSON."""
        from src.planner_agent.runtime.agent_card import create_marathon_planner_card

        card = create_marathon_planner_card()
        card_dict = card.model_dump()
        json_str = json.dumps(card_dict)

        assert len(json_str) > 0
        assert "planner_agent" in json_str


class TestMarathonPlannerExecutor:
    """Test Marathon Planner executor."""

    def test_executor_class_exists(self):
        """Test executor class can be imported."""
        from src.planner_agent.runtime.agent_executor import MarathonPlannerExecutor

        assert MarathonPlannerExecutor is not None

    def test_executor_can_be_instantiated(self):
        """Test executor can be created."""
        from src.planner_agent.runtime.agent_executor import MarathonPlannerExecutor

        executor = MarathonPlannerExecutor()
        assert executor is not None
        assert executor.agent is None  # Lazy init


class TestMarathonPlannerMemory:
    """Test Marathon Planner memory manager."""

    def test_memory_topics_creation(self):
        """Test custom memory topics can be created."""
        from src.planner_agent.services.memory_manager import (
            create_marathon_planner_memory_topics,
        )

        config = create_marathon_planner_memory_topics()
        assert config is not None
        assert config.memory_topics is not None
        assert len(config.memory_topics) == 4

    def test_memory_topic_labels(self):
        """Test memory topics have correct labels."""
        from src.planner_agent.services.memory_manager import (
            create_marathon_planner_memory_topics,
        )

        config = create_marathon_planner_memory_topics()
        labels = [t.custom_memory_topic.label for t in config.memory_topics]
        assert "planning_history" in labels
        assert "user_preferences" in labels
        assert "route_patterns" in labels
        assert "logistics_insights" in labels

    @pytest.mark.skipif(
        not os.environ.get("GOOGLE_CLOUD_PROJECT"),
        reason="Requires GOOGLE_CLOUD_PROJECT",
    )
    def test_create_memory_service_without_agent_engine(self):
        """Test memory service returns None without AGENT_ENGINE_ID."""
        from src.planner_agent.services.memory_manager import create_memory_service

        old_val = os.environ.pop("AGENT_ENGINE_ID", None)
        try:
            service = create_memory_service()
            assert service is None
        finally:
            if old_val:
                os.environ["AGENT_ENGINE_ID"] = old_val


class TestMarathonPlannerSession:
    """Test Marathon Planner session manager."""

    def test_ttl_cache(self):
        """Test TTL cache basic operations."""
        from src.planner_agent.services.session_manager import TTLCache

        cache = TTLCache(maxsize=10, ttl=60)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
        assert "key1" in cache
        assert len(cache) == 1

    def test_session_service_creation_local(self):
        """Test session service defaults to InMemory for local dev."""
        from src.planner_agent.services.session_manager import create_session_service
        from google.adk.sessions import InMemorySessionService

        old_val = os.environ.pop("AGENT_ENGINE_ID", None)
        try:
            service = create_session_service()
            assert isinstance(service, InMemorySessionService)
        finally:
            if old_val:
                os.environ["AGENT_ENGINE_ID"] = old_val


class TestMarathonPlannerModuleStructure:
    """Test Marathon Planner follows the standard module structure."""

    def test_agent_subdir_exists(self):
        """Test agent/ subdirectory exists."""
        assert (AGENT_ROOT / "core").is_dir()

    def test_skills_subdir_exists(self):
        """Test skills/ subdirectory exists."""
        assert (AGENT_ROOT / "skills").is_dir()

    def test_runtime_subdir_exists(self):
        """Test runtime/ subdirectory exists."""
        assert (AGENT_ROOT / "runtime").is_dir()

    def test_services_subdir_exists(self):
        """Test services/ subdirectory exists."""
        assert (AGENT_ROOT / "services").is_dir()

    def test_skill_directories_exist(self):
        """Test consolidated skill directories exist."""
        skills_dir = AGENT_ROOT / "skills"
        expected_skills = [
            "route-planning",
            "plan-evaluation",
        ]
        for skill_name in expected_skills:
            assert (skills_dir / skill_name).is_dir(), f"Missing skill: {skill_name}"

    def test_skill_md_files_exist(self):
        """Test all skills have SKILL.md files."""
        skills_dir = AGENT_ROOT / "skills"
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
                assert (skill_dir / "SKILL.md").is_file(), f"Missing SKILL.md in {skill_dir.name}"

    def test_prompts_module_exists(self):
        """Test prompts.py exists in agent/."""
        assert (AGENT_ROOT / "core" / "prompts.py").is_file()

    def test_agent_card_in_runtime(self):
        """Test agent_card.py is in runtime/."""
        assert (AGENT_ROOT / "runtime" / "agent_card.py").is_file()

    def test_session_manager_in_services(self):
        """Test session_manager.py is in services/."""
        assert (AGENT_ROOT / "services" / "session_manager.py").is_file()

    def test_memory_manager_in_services(self):
        """Test memory_manager.py is in services/."""
        assert (AGENT_ROOT / "services" / "memory_manager.py").is_file()

    def test_executor_class_exists(self):
        """Test executor class exists in runtime/."""
        from src.planner_agent.runtime.agent_executor import MarathonPlannerExecutor

        assert MarathonPlannerExecutor is not None

    def test_auth_in_agent(self):
        """Test auth.py is in agent/."""
        assert (AGENT_ROOT / "core" / "auth.py").is_file()

    def test_dockerfile_at_root(self):
        """Test Dockerfile stays at agent root (for terraform)."""
        assert (AGENT_ROOT / "Dockerfile").is_file()

    def test_main_at_root(self):
        """Test main.py stays at agent root (Cloud Run entry point)."""
        assert (AGENT_ROOT / "main.py").is_file()


class TestMarathonPlannerCloudRunIntegration:
    """Test Cloud Run deployment integration."""

    def test_main_py_imports_from_runtime(self):
        """Test main.py imports from runtime/ subdirectory."""
        main_content = (AGENT_ROOT / "main.py").read_text()
        assert "from .runtime.agent_card import" in main_content
        assert "from .runtime.agent_executor import" in main_content

    def test_dockerfile_references_main(self):
        """Test Dockerfile CMD references the correct module."""
        dockerfile_content = (AGENT_ROOT / "Dockerfile").read_text()
        assert "src.planner_agent.main:app" in dockerfile_content

    def test_agent_executor_imports_from_services(self):
        """Test executor imports from services/ subdirectory."""
        executor_content = (AGENT_ROOT / "runtime" / "agent_executor.py").read_text()
        assert "from ..services.memory_manager import" in executor_content
        assert "from ..services.session_manager import" in executor_content

    def test_agent_imports_from_services(self):
        """Test agent.py imports from services/ subdirectory."""
        agent_content = (AGENT_ROOT / "core" / "agent.py").read_text()
        assert "from ..services.memory_manager import" in agent_content
