"""Tests for the Simulation Controller Agent.

Tests agent creation, schemas, skills, tools, and module structure.

Usage:
    uv run pytest tests/test_simulator_agent.py -v
"""

import json
import pathlib

import pytest
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Schema tests
# ============================================================================


class TestSimulationControllerSchemas:
    """Test Simulation Controller Agent schemas."""

    def test_simulation_approval_approved(self):
        from src.simulator_agent.core.schemas import SimulationApproval

        approval = SimulationApproval(
            approved=True,
            overall_readiness=0.92,
            route_feasibility="feasible",
            logistics_readiness="ready",
            safety_clearance="cleared",
            blockers=[],
            recommendations=["Consider adding extra water stations"],
            summary="Plan is ready for simulation",
        )
        assert approval.approved is True
        assert approval.overall_readiness == 0.92
        assert approval.route_feasibility == "feasible"
        assert len(approval.blockers) == 0

    def test_simulation_approval_rejected(self):
        from src.simulator_agent.core.schemas import SimulationApproval

        approval = SimulationApproval(
            approved=False,
            overall_readiness=0.45,
            route_feasibility="infeasible",
            logistics_readiness="not_ready",
            safety_clearance="blocked",
            blockers=["Route blocks hospital access", "No water stations specified"],
            recommendations=[],
            summary="Plan has critical issues",
        )
        assert approval.approved is False
        assert approval.overall_readiness == 0.45
        assert len(approval.blockers) == 2

    def test_simulation_approval_conditional(self):
        from src.simulator_agent.core.schemas import SimulationApproval

        approval = SimulationApproval(
            approved=False,
            overall_readiness=0.72,
            route_feasibility="feasible",
            logistics_readiness="partial",
            safety_clearance="conditional",
            blockers=[],
            recommendations=["Add medical tents at mile 15 and 20"],
            summary="Plan needs minor improvements",
        )
        assert approval.approved is False
        assert 0.6 <= approval.overall_readiness <= 0.85
        assert len(approval.recommendations) == 1

    def test_simulation_approval_readiness_bounds(self):
        from src.simulator_agent.core.schemas import SimulationApproval

        with pytest.raises(Exception):
            SimulationApproval(
                approved=False,
                overall_readiness=1.5,
                route_feasibility="feasible",
                logistics_readiness="ready",
                safety_clearance="cleared",
            )

        with pytest.raises(Exception):
            SimulationApproval(
                approved=False,
                overall_readiness=-0.1,
                route_feasibility="feasible",
                logistics_readiness="ready",
                safety_clearance="cleared",
            )

    def test_simulation_approval_defaults(self):
        from src.simulator_agent.core.schemas import SimulationApproval

        approval = SimulationApproval(
            approved=True,
            overall_readiness=0.9,
            route_feasibility="feasible",
            logistics_readiness="ready",
            safety_clearance="cleared",
        )
        assert approval.blockers == []
        assert approval.recommendations == []
        assert approval.summary == ""

    def test_simulation_approval_serializes_to_json(self):
        from src.simulator_agent.core.schemas import SimulationApproval

        approval = SimulationApproval(
            approved=True,
            overall_readiness=0.88,
            route_feasibility="feasible",
            logistics_readiness="ready",
            safety_clearance="cleared",
            summary="Good plan",
        )
        data = approval.model_dump()
        json_str = json.dumps(data)
        assert "0.88" in json_str
        assert "feasible" in json_str

    def test_schemas_importable_from_top_level(self):
        from src.schemas import SimulationApproval

        assert SimulationApproval is not None


# ============================================================================
# Config tests
# ============================================================================


class TestSimulationControllerConfig:
    """Test Simulation Controller Agent configuration."""

    def test_agent_name(self):
        from src.simulator_agent.core.config import AGENT_NAME

        assert AGENT_NAME == "simulator_agent"

    def test_model_default(self):
        from src.simulator_agent.core.config import MODEL

        assert "gemini" in MODEL.lower()

    def test_output_schema(self):
        from src.simulator_agent.core.config import OUTPUT_SCHEMA

        assert OUTPUT_SCHEMA.__name__ == "SimulationApproval"

    def test_description_is_nonempty(self):
        from src.simulator_agent.core.config import AGENT_DESCRIPTION

        assert len(AGENT_DESCRIPTION) > 20
        assert "simulation" in AGENT_DESCRIPTION.lower()

    def test_instruction_is_nonempty(self):
        from src.simulator_agent.core.prompts import INSTRUCTION

        assert len(INSTRUCTION) > 100
        assert "simulation" in INSTRUCTION.lower()

    def test_instruction_mentions_skill(self):
        from src.simulator_agent.core.prompts import INSTRUCTION

        assert "review-marathon-plan" in INSTRUCTION.lower()

    def test_instruction_mentions_review_criteria(self):
        from src.simulator_agent.core.prompts import INSTRUCTION

        instruction_lower = INSTRUCTION.lower()
        assert "route data" in instruction_lower
        assert "logistics data" in instruction_lower
        assert "safety clearance" in instruction_lower

    def test_instruction_mentions_approval_thresholds(self):
        from src.simulator_agent.core.prompts import INSTRUCTION

        assert "Approved" in INSTRUCTION
        assert "Rejected" in INSTRUCTION


# ============================================================================
# Tools tests
# ============================================================================


class TestSimulationControllerTools:
    """Test FunctionTool computation functions."""

    @pytest.mark.asyncio
    async def test_check_plan_readiness_complete_plan(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        plan = (
            "Route distance: 26.2 miles through downtown Las Vegas. "
            "22 water stations every 1.2 miles. "
            "Medical tent at miles 5, 10, 15, 20, and finish. "
            "Chip timing with tracking mats. "
            "Start line at Convention Center, finish line at Fremont Street. "
            "Emergency vehicle crossings every 2 miles. "
            "Budget: $1.5M with revenue from registration. "
            "Race day schedule starts at 5am setup."
        )
        result = await check_plan_readiness(plan)
        assert result["readiness_score"] == 1.0
        assert result["passed_checks"] == result["total_checks"]
        assert len(result["missing_elements"]) == 0

    @pytest.mark.asyncio
    async def test_check_plan_readiness_incomplete_plan(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        plan = "A marathon through Las Vegas."
        result = await check_plan_readiness(plan)
        assert result["readiness_score"] < 1.0
        assert len(result["missing_elements"]) > 0

    @pytest.mark.asyncio
    async def test_check_plan_readiness_distance_detection_miles(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Route is 26.2 miles long")
        assert result["checklist"]["distance_specified"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_distance_detection_km(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Route is 42.195 kilometers long")
        assert result["checklist"]["distance_specified"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_wrong_distance(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Route is 10 miles long")
        # In the refactored 'fast check', we only care about presence,
        # so this should now be True.
        assert result["checklist"]["distance_specified"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_water_stations(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("20 water station locations along the route")
        assert result["checklist"]["water_stations"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_medical(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Medical tent at mile 10 and first aid at mile 20")
        assert result["checklist"]["medical_tents"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_timing(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Chip timing system with tracking")
        assert result["checklist"]["timing_system"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_start_finish(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Start line at park, finish line downtown")
        assert result["checklist"]["start_finish"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_emergency(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Emergency vehicle access at every crossing")
        assert result["checklist"]["emergency_access"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_budget(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Total budget of $2M with cost breakdown")
        assert result["checklist"]["budget_included"] is True

    @pytest.mark.asyncio
    async def test_check_plan_readiness_timeline(self):
        from src.simulator_agent.core.tools import check_plan_readiness

        result = await check_plan_readiness("Race day schedule begins at 4am")
        assert result["checklist"]["timeline_included"] is True

    def test_get_tools_returns_list(self):
        from src.simulator_agent.core.tools import get_tools

        tools = get_tools()
        assert isinstance(tools, list)
        assert len(tools) == 1
        assert callable(tools[0])


# ============================================================================
# Skills tests
# ============================================================================


class TestSimulationControllerSkills:
    """Test ADK Skills for the Simulation Controller Agent."""

    @pytest.fixture
    def skills_dir(self):
        return pathlib.Path("src/simulator_agent/skills")

    def test_review_skill_loads(self, skills_dir):
        from google.adk.skills import load_skill_from_dir

        skill = load_skill_from_dir(skills_dir / "review-marathon-plan")
        assert skill.name == "review-marathon-plan"
        assert "review" in skill.description.lower()

    def test_review_skill_has_references(self, skills_dir):
        refs = skills_dir / "review-marathon-plan" / "references"
        assert (refs / "review_checklist.md").exists()

    def test_review_skill_has_scripts(self, skills_dir):
        scripts = skills_dir / "review-marathon-plan" / "scripts"
        assert (scripts / "check_readiness.py").exists()

    def test_review_skill_references_loaded(self, skills_dir):
        from google.adk.skills import load_skill_from_dir

        skill = load_skill_from_dir(skills_dir / "review-marathon-plan")
        refs = skill.resources.references
        assert "review_checklist.md" in refs

    def test_skill_toolset_creation(self, skills_dir):
        from google.adk.skills import load_skill_from_dir
        from google.adk.tools.skill_toolset import SkillToolset

        skill = load_skill_from_dir(skills_dir / "review-marathon-plan")
        toolset = SkillToolset(skills=[skill])
        assert toolset is not None


# ============================================================================
# Agent construction tests
# ============================================================================


class TestSimulationControllerAgent:
    """Test Simulation Controller Agent construction."""

    def test_root_agent_importable(self):
        from src.simulator_agent.core.agent import root_agent

        assert root_agent is not None

    def test_agent_name(self):
        from src.simulator_agent.core.agent import root_agent

        assert root_agent.name == "simulator_agent"

    def test_agent_has_skill_toolset(self):
        from google.adk.tools.skill_toolset import SkillToolset

        from src.simulator_agent.core.agent import root_agent

        has_skills = any(isinstance(t, SkillToolset) for t in root_agent.tools)
        assert has_skills

    def test_agent_has_function_tools(self):
        from src.simulator_agent.core.agent import root_agent

        assert len(root_agent.tools) >= 3  # SkillToolset + PreloadMemory + check_plan_readiness

    def test_agent_has_output_schema(self):
        from src.simulator_agent.core.agent import root_agent

        assert root_agent.output_schema is not None
        assert root_agent.output_schema.__name__ == "SimulationApproval"

    def test_agent_importable_from_top_level(self):
        from src.simulator_agent import root_agent

        assert root_agent is not None


# ============================================================================
# Module structure tests
# ============================================================================


class TestSimulationControllerModuleStructure:
    """Test the module structure."""

    def test_agent_subdir_exists(self):
        assert pathlib.Path("src/simulator_agent/core").is_dir()

    def test_skills_subdir_exists(self):
        assert pathlib.Path("src/simulator_agent/skills").is_dir()

    def test_runtime_subdir_exists(self):
        assert pathlib.Path("src/simulator_agent/runtime").is_dir()

    def test_services_subdir_exists(self):
        assert pathlib.Path("src/simulator_agent/services").is_dir()

    def test_skill_directory_exists(self):
        skills = pathlib.Path("src/simulator_agent/skills")
        assert (skills / "review-marathon-plan").is_dir()

    def test_skill_md_file_exists(self):
        skills = pathlib.Path("src/simulator_agent/skills")
        assert (skills / "review-marathon-plan" / "SKILL.md").exists()

    def test_prompts_module_exists(self):
        assert pathlib.Path("src/simulator_agent/core/prompts.py").exists()

    def test_agent_card_in_runtime(self):
        from src.simulator_agent.runtime.agent_card import create_simulation_controller_card

        card = create_simulation_controller_card()
        assert card.name == "simulator_agent"

    def test_session_manager_in_services(self):
        from src.simulator_agent.services.session_manager import TTLCache

        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_memory_manager_in_services(self):
        from src.simulator_agent.services.memory_manager import create_simulation_controller_memory_topics

        topics = create_simulation_controller_memory_topics()
        assert topics is not None
        assert len(topics.memory_topics) == 2

    def test_memory_topic_labels(self):
        from src.simulator_agent.services.memory_manager import create_simulation_controller_memory_topics

        config = create_simulation_controller_memory_topics()
        labels = [t.custom_memory_topic.label for t in config.memory_topics]
        assert "approval_history" in labels
        assert "readiness_patterns" in labels

    def test_executor_class_exists(self):
        from src.simulator_agent.runtime.agent_executor import SimulationControllerExecutor

        executor = SimulationControllerExecutor()
        assert executor.agent is None  # Lazy init


# ============================================================================
# Marathon Planner integration tests
# ============================================================================


class TestMarathonPlannerSimulationControllerIntegration:
    """Test Marathon Planner's simulation controller A2A tool integration."""

    def test_marathon_planner_has_simulation_controller_creator(self):
        from src.planner_agent.core.tools import create_simulation_controller_tool

        assert callable(create_simulation_controller_tool)

    def test_marathon_planner_instruction_mentions_simulation(self):
        from src.planner_agent.core.prompts import INSTRUCTION

        assert "simulation" in INSTRUCTION.lower()
