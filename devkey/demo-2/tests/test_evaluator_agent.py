"""Tests for the Evaluator Agent (refactored with ADK Skills).

Tests agent creation, schemas, skills, tools, metrics, and module structure.

Usage:
    uv run pytest tests/test_evaluator_agent.py -v
"""

import json
import os
import pathlib
import subprocess

import pytest
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# Schema tests
# ============================================================================


class TestEvaluatorSchemas:
    """Test Evaluator Agent schemas."""

    def test_evaluation_finding_schema(self):
        from src.planner_agent.evaluator.schemas import EvaluationFinding

        finding = EvaluationFinding(
            criterion="safety_compliance",
            severity="high",
            description="Route blocks hospital access",
        )
        assert finding.criterion == "safety_compliance"
        assert finding.severity == "high"

    def test_evaluation_result_passed(self):
        from src.planner_agent.evaluator.schemas import EvaluationResult

        result = EvaluationResult(
            passed=True,
            overall_score=0.91,
            scores={"safety_compliance": 0.95, "community_impact": 0.88},
            findings=[],
            improvement_suggestions=[],
            iteration_number=2,
            summary="Plan passes all criteria",
        )
        assert result.passed is True
        assert result.overall_score == 0.91
        assert result.iteration_number == 2

    def test_evaluation_result_failed(self):
        from src.planner_agent.evaluator.schemas import EvaluationResult, EvaluationFinding

        finding = EvaluationFinding(
            criterion="logistics_completeness",
            severity="medium",
            description="Missing water station details",
        )
        result = EvaluationResult(
            passed=False,
            overall_score=0.62,
            scores={"logistics_completeness": 0.4},
            findings=[finding],
            improvement_suggestions=["Add water stations every 1.5 miles"],
            summary="Plan needs logistics improvements",
        )
        assert result.passed is False
        assert len(result.findings) == 1

    def test_evaluation_result_serializes_to_json(self):
        from src.planner_agent.evaluator.schemas import EvaluationResult

        result = EvaluationResult(
            passed=True,
            overall_score=0.88,
            scores={"safety_compliance": 0.9},
            summary="Good plan",
        )
        data = result.model_dump()
        json_str = json.dumps(data)
        assert "0.88" in json_str

    def test_evaluation_criteria_list(self):
        from src.planner_agent.evaluator.schemas import EVALUATION_CRITERIA

        assert len(EVALUATION_CRITERIA) == 7
        assert "safety_compliance" in EVALUATION_CRITERIA
        assert "distance_compliance" in EVALUATION_CRITERIA

    def test_schemas_importable_from_top_level(self):
        from src.schemas import EvaluationResult, EvaluationFinding

        assert EvaluationResult is not None
        assert EvaluationFinding is not None


# ============================================================================
# Config tests
# ============================================================================


class TestEvaluatorConfig:
    """Test Evaluator Agent configuration."""

    def test_agent_name(self):
        from src.planner_agent.evaluator.agent import AGENT_NAME

        assert AGENT_NAME == "evaluator_agent"

    def test_model_default(self):
        from src.planner_agent.evaluator.agent import MODEL

        assert "gemini" in MODEL.lower()

    def test_output_schema(self):
        from src.planner_agent.evaluator.agent import OUTPUT_SCHEMA

        assert OUTPUT_SCHEMA.__name__ == "EvaluationResult"

    def test_criterion_weights_sum_to_one(self):
        from src.planner_agent.evaluator.agent import CRITERION_WEIGHTS

        total = sum(CRITERION_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_criterion_weights_has_all_criteria(self):
        from src.planner_agent.evaluator.agent import CRITERION_WEIGHTS

        assert len(CRITERION_WEIGHTS) == 7

    def test_instruction_is_nonempty(self):
        from src.planner_agent.evaluator.prompts import INSTRUCTION

        assert len(INSTRUCTION) > 100
        assert "evaluat" in INSTRUCTION.lower()

    def test_instruction_mentions_phases(self):
        from src.planner_agent.evaluator.prompts import INSTRUCTION

        instruction_lower = INSTRUCTION.lower()
        assert "evaluation methodology" in instruction_lower
        assert "score interpretation" in instruction_lower
        assert "improvement strategy" in instruction_lower

    def test_description_is_nonempty(self):
        from src.planner_agent.evaluator.agent import AGENT_DESCRIPTION

        assert len(AGENT_DESCRIPTION) > 20


# ============================================================================
# FunctionTool tests
# ============================================================================


class TestEvaluatorTools:
    """Test FunctionTool computation functions."""

    async def test_evaluate_plan_invalid_json(self):
        from src.planner_agent.evaluator.tools import evaluate_plan

        result = await evaluate_plan("not valid json")
        assert result["passed"] is False
        assert result["overall_score"] == 0.0
        assert result["eval_method"] == "error"

    async def test_evaluate_plan_good_plan(self):
        from src.planner_agent.evaluator.tools import evaluate_plan

        request = json.dumps({
            "user_intent": "Plan a scenic marathon through downtown Chicago in October",
            "proposed_plan": (
                "Route starts at Grant Park in Chicago, follows Lake Shore Drive "
                "for scenic lakefront views. Total distance: 26.2 miles. "
                "Emergency vehicle crossings at every 2-mile interval. "
                "22 water stations. Chip timing. Community cheer zones. "
                "Budget: $1.5M costs, $2.2M revenue from registration and sponsors."
            ),
        })

        result = await evaluate_plan(request)
        assert result["eval_method"] in ("heuristic", "vertex_ai_eval")
        assert result["overall_score"] > 0.0
        assert "scores" in result

    async def test_evaluate_plan_heuristic_unsafe(self):
        from src.planner_agent.evaluator.tools import evaluate_plan

        request = json.dumps({
            "user_intent": "Plan a fast marathon in Chicago",
            "proposed_plan": (
                "Route blocks hospital access with no detour. "
                "Distance: 25 miles. We'll skip the rest."
            ),
        })

        result = await evaluate_plan(request)
        assert result["passed"] is False
        assert len(result["findings"]) > 0

    def test_heuristic_distance_compliance(self):
        from src.planner_agent.evaluator.tools import _heuristic_eval

        scores, details = _heuristic_eval(
            "Plan a marathon in Chicago",
            "Route distance: 25 miles through downtown Chicago"
        )
        assert scores["distance_compliance"] < 50

    def test_heuristic_intent_alignment(self):
        from src.planner_agent.evaluator.tools import _heuristic_eval

        scores, details = _heuristic_eval(
            "Plan a scenic marathon in Chicago",
            "This marathon takes place in Houston, Texas. Distance: 26.2 miles."
        )
        assert scores["intent_alignment"] < 60

    def test_build_result_passed(self):
        from src.planner_agent.evaluator.tools import _build_result

        scores = {
            "safety_compliance": 95.0,
            "community_impact": 90.0,
            "logistics_completeness": 88.0,
            "financial_viability": 92.0,
            "participant_experience": 85.0,
            "intent_alignment": 95.0,
            "distance_compliance": 100.0,
        }
        result = _build_result(scores, {}, "heuristic")
        assert result["passed"] is True
        assert result["overall_score"] >= 85.0

    def test_build_result_failed(self):
        from src.planner_agent.evaluator.tools import _build_result

        scores = {
            "safety_compliance": 0.3,
            "community_impact": 0.5,
            "logistics_completeness": 0.4,
            "financial_viability": 0.3,
            "participant_experience": 0.5,
            "intent_alignment": 0.2,
            "distance_compliance": 0.2,
        }
        result = _build_result(scores, {}, "heuristic")
        assert result["passed"] is False
        assert len(result["findings"]) > 0
        assert len(result["improvement_suggestions"]) > 0

    def test_suggest_improvement(self):
        from src.planner_agent.evaluator.tools import _suggest_improvement

        suggestion = _suggest_improvement("safety_compliance", 0.3, "")
        assert len(suggestion) > 0
        assert "emergency" in suggestion.lower()


# ============================================================================
# Metrics tests
# ============================================================================


class TestEvaluatorMetrics:
    """Test custom Vertex AI Eval metric creation."""

    def test_safety_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_safety_compliance_metric

        metric = _create_safety_compliance_metric()
        assert metric.name == "safety_compliance"

    def test_community_impact_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_community_impact_metric

        metric = _create_community_impact_metric()
        assert metric.name == "community_impact"

    def test_logistics_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_logistics_completeness_metric

        metric = _create_logistics_completeness_metric()
        assert metric.name == "logistics_completeness"

    def test_financial_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_financial_viability_metric

        metric = _create_financial_viability_metric()
        assert metric.name == "financial_viability"

    def test_experience_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_participant_experience_metric

        metric = _create_participant_experience_metric()
        assert metric.name == "participant_experience"

    def test_intent_alignment_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_intent_alignment_metric

        metric = _create_intent_alignment_metric()
        assert metric.name == "intent_alignment"

    def test_distance_compliance_metric_creation(self):
        from src.planner_agent.evaluator.tools import _create_distance_compliance_metric

        metric = _create_distance_compliance_metric()
        assert metric.name == "distance_compliance"
        assert metric.custom_function is not None


# ============================================================================
# Agent construction tests
# ============================================================================


class TestEvaluatorAgent:
    """Test Evaluator Agent construction."""

    def test_root_agent_importable(self):
        from src.planner_agent.evaluator.agent import root_agent

        assert root_agent is not None

    def test_agent_name(self):
        from src.planner_agent.evaluator.agent import root_agent

        assert root_agent.name == "evaluator_agent"

    def test_agent_has_function_tools(self):
        from src.planner_agent.evaluator.agent import root_agent

        assert len(root_agent.tools) >= 2  # PreloadMemory + evaluate_plan

    def test_agent_has_output_schema(self):
        from src.planner_agent.evaluator.agent import root_agent

        assert root_agent.output_schema is not None
        assert root_agent.output_schema.__name__ == "EvaluationResult"

    def test_agent_importable_from_top_level(self):
        from src.planner_agent.evaluator import root_agent

        assert root_agent is not None


# ============================================================================
# Module structure tests
# ============================================================================


class TestEvaluatorModuleStructure:
    """Test the refactored module structure."""

    def test_agent_subdir_exists(self):
        assert pathlib.Path("src/planner_agent/evaluator").is_dir()

    def test_services_subdir_exists(self):
        assert pathlib.Path("src/planner_agent/evaluator/services").is_dir()

    def test_prompts_module_exists(self):
        assert pathlib.Path("src/planner_agent/evaluator/prompts.py").exists()

    def test_session_manager_in_services(self):
        from src.planner_agent.evaluator.services.session_manager import TTLCache

        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"


# ============================================================================
# Marathon Planner integration tests
# ============================================================================


class TestMarathonPlannerEvaluatorIntegration:
    """Test Marathon Planner's evaluator A2A tool integration."""

    def test_marathon_planner_has_evaluator_creator(self):
        from src.planner_agent.core.tools import create_evaluator_tool

        assert callable(create_evaluator_tool)

    def test_marathon_planner_instruction_mentions_evaluator(self):
        from src.planner_agent.core.prompts import INSTRUCTION

        assert "evaluator" in INSTRUCTION.lower()
        assert any(kw in INSTRUCTION.lower() for kw in ["passed", "passes", "successful"])
