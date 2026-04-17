"""Tools for the Evaluator Agent.

Provides tools for evaluating marathon plans using Vertex AI Evaluation
with custom metrics. Uses a hybrid approach: LLM-based evaluation with
custom rubrics, plus deterministic checks, with heuristic fallback.
"""

import asyncio
import json
import os
import re
from typing import Any

import logging
import pandas as pd
import vertexai
from google.genai import types as genai_types
from vertexai import types
from .agent import CRITERION_WEIGHTS, SEVERITY_THRESHOLDS, MODEL
from .schemas import EvaluationResult


logger = logging.getLogger(__name__)

def _get_model_resource() -> str:
    """Get the full resource path for the Vertex AI evaluation model."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    return f"projects/{project_id}/locations/{location}/publishers/google/models/{MODEL}" if project_id else MODEL

# ============================================================================
# MAIN EVALUATION TOOL
# ============================================================================


async def evaluate_plan(
    evaluation_request: str,
) -> dict[str, Any]:
    """Evaluate a proposed marathon plan across quality criteria.

    Uses Vertex AI Evaluation with 7 custom metrics.
    Falls back to heuristic evaluation if Vertex AI Eval API fails.

    Args:
        evaluation_request: JSON string with user_intent and proposed_plan

    Returns:
        dict with evaluation results
    """
    try:
        request_data = json.loads(evaluation_request)
    except json.JSONDecodeError as e:
        return {
            "passed": False,
            "scores": {},
            "findings": [
                {
                    "criterion": "intent_alignment",
                    "description": f"Invalid JSON input: {e}",
                    "severity": "high",
                }
            ],
            "improvement_suggestions": [
                "Provide valid JSON with 'user_intent' and 'proposed_plan' fields."
            ],
            "overall_score": 0.0,
            "eval_method": "error",
        }

    user_intent_raw = request_data.get("user_intent", "Unknown intent")
    proposed_plan_raw = request_data.get("proposed_plan", "No plan provided")

    user_intent = json.dumps(user_intent_raw) if not isinstance(user_intent_raw, str) else user_intent_raw
    proposed_plan = json.dumps(proposed_plan_raw) if not isinstance(proposed_plan_raw, str) else proposed_plan_raw

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if project_id:
        try:
            scores, details = await _run_custom_eval(
                project_id=project_id,
                location=location,
                user_intent=user_intent,
                proposed_plan=proposed_plan,
            )
            return _build_result(scores, details, eval_method="vertex_ai_eval")
        except Exception as e:
            logger.warning(f"Vertex AI Eval failed, using heuristics: {e}")

    scores, details = _heuristic_eval(user_intent, proposed_plan)
    return _build_result(scores, details, eval_method="heuristic")


# ============================================================================
# CUSTOM METRICS DEFINITIONS
# ============================================================================


def _create_safety_compliance_metric() -> types.LLMMetric:
    """Evaluate emergency corridor access and crowd safety."""
    builder = types.MetricPromptBuilder(
        metric_definition=(
            "Evaluate whether the proposed marathon route maintains emergency "
            "vehicle access and crowd safety. Check for blocked hospitals, fire stations, "
            "and major emergency corridors."
        ),
        criteria={
            "Emergency corridor access": (
                "The route does not permanently block access to hospitals, "
                "fire stations, or police stations without providing clear detour routes."
            ),
            "Evacuation routes": (
                "Major evacuation routes remain accessible or have documented alternatives."
            ),
            "Emergency vehicle passage": (
                "The plan includes provisions for emergency vehicle crossing "
                "at regular intervals along the route."
            ),
        },
        rating_scores={
            "1": "Dangerous - Major emergency corridors blocked with no detours",
            "25": "Unsafe - Several emergency access points compromised",
            "50": "Concerning - Some emergency access issues that need resolution",
            "75": "Mostly safe - Minor emergency access concerns, easy to fix",
            "100": "Fully safe - Emergency access maintained throughout",
        },
    )

    return types.LLMMetric(
        name="safety_compliance",
        prompt_template=str(builder),
        judge_model=_get_model_resource(),
    )


def _create_community_impact_metric() -> types.LLMMetric:
    """Evaluate community disruption, inclusivity, and neighborhood equity."""
    builder = types.MetricPromptBuilder(
        metric_definition=(
            "Evaluate the marathon plan's impact on the local community. "
            "Check for noise disruption, residential access, business impact, "
            "inclusivity, and equitable neighborhood treatment."
        ),
        criteria={
            "Residential disruption": (
                "The plan minimizes disruption to residential areas, with "
                "reasonable timing and notification plans."
            ),
            "Business access": (
                "Local businesses along the route can still operate or have "
                "been accommodated with alternative access."
            ),
            "Neighborhood equity": (
                "The route and plan are accessible to diverse communities "
                "and do not disproportionately burden any demographic group."
            ),
            "Community engagement": (
                "The plan includes cheer zones, community events, or other "
                "ways to involve and benefit local residents."
            ),
        },
        rating_scores={
            "1": "Harmful - Major negative impact on community with no mitigation",
            "25": "Disruptive - Significant community issues that need resolution",
            "50": "Mixed - Some community concerns that need attention",
            "75": "Considerate - Minor community impacts with good mitigation",
            "100": "Excellent - Community benefits from the event",
        },
    )

    return types.LLMMetric(
        name="community_impact",
        prompt_template=str(builder),
        judge_model=_get_model_resource(),
    )


def _create_logistics_completeness_metric() -> types.LLMMetric:
    """Evaluate logistics coverage: water stations, timing, marshals, equipment."""
    builder = types.MetricPromptBuilder(
        metric_definition=(
            "Evaluate whether the marathon plan's logistics are complete and "
            "adequate for the expected scale. Check water stations, timing systems, "
            "course marshals, start/finish infrastructure, and equipment."
        ),
        criteria={
            "Water and nutrition": (
                "Hydration and nutrition are considered for the expected participant count."
            ),
            "Timing and tracking": (
                "Timing systems (chip timing, mats) are specified. "
                "Tracking for runner safety is planned."
            ),
            "Course management": (
                "Sufficient course marshals, signage, barriers, and traffic control "
                "are planned for safe runner flow."
            ),
            "Start/finish infrastructure": (
                "Start/finish areas have adequate capacity for the participant count, "
                "with corrals, stages, and post-race areas."
            ),
        },
        rating_scores={
            "1": "Incomplete - Critical logistics missing (no water, no timing)",
            "25": "Sparse - Major logistics gaps that could impact safety",
            "50": "Partial - Some logistics covered but significant gaps remain",
            "75": "Mostly complete - Minor logistics details to finalize",
            "100": "Comprehensive - All logistics thoroughly planned",
        },
    )

    return types.LLMMetric(
        name="logistics_completeness",
        prompt_template=str(builder),
        judge_model=_get_model_resource(),
    )


def _create_financial_viability_metric() -> types.LLMMetric:
    """Evaluate budget balance, revenue sources, and cost control."""
    builder = types.MetricPromptBuilder(
        metric_definition=(
            "Evaluate the financial viability of the marathon plan. "
            "Check budget balance, revenue sources, cost estimates, "
            "sponsorship opportunities, and financial sustainability."
        ),
        criteria={
            "Budget balance": (
                "Revenue projections (registration, sponsorship, merchandise) "
                "meet or exceed estimated costs."
            ),
            "Cost estimates": (
                "Cost estimates are realistic and cover major expense categories "
                "(permits, equipment, staffing, prizes, insurance)."
            ),
            "Revenue diversity": (
                "Revenue comes from multiple sources, not just registration fees. "
                "Sponsorship, merchandise, and media rights are considered."
            ),
        },
        rating_scores={
            "1": "Unviable - Major financial gaps, likely to lose significant money",
            "25": "Risky - Budget concerns that could threaten event viability",
            "50": "Uncertain - Financial plan needs more detail and validation",
            "75": "Viable - Sound financial plan with minor gaps",
            "100": "Strong - Well-balanced budget with diverse revenue streams",
        },
    )

    return types.LLMMetric(
        name="financial_viability",
        prompt_template=str(builder),
        judge_model=_get_model_resource(),
    )


def _create_participant_experience_metric() -> types.LLMMetric:
    """Evaluate route quality, scenic value, and runner amenities."""
    builder = types.MetricPromptBuilder(
        metric_definition=(
            "Evaluate the participant experience of a proposed marathon plan. "
            "Check for route quality, scenic value, spectator access, runner amenities, "
            "and overall experience."
        ),
        criteria={
            "Route Quality": "The route surface is suitable for running and the elevation profile is appropriate for the event type.",
            "Scenic Value": "The route passes through interesting, attractive, or landmark areas.",
            "Spectator Access": "There are good viewing areas for spectators to cheer runners.",
            "Runner Amenities": "Post-race amenities (food, medals, recovery area) are planned.",
            "Overall Experience": "Runners would enjoy this event and recommend it.",
        },
        rating_scores={
            "1": "Poor experience - Boring route, no amenities, unpleasant conditions",
            "25": "Below average - Significant experience gaps",
            "50": "Average - Adequate but unremarkable experience",
            "75": "Good - Enjoyable route with good amenities",
            "100": "Excellent - Outstanding experience that runners will remember",
        },
    )

    return types.LLMMetric(
        name="participant_experience",
        prompt_template=str(builder),
        judge_model=_get_model_resource(),
    )


def _create_intent_alignment_metric() -> types.LLMMetric:
    """Evaluate whether the plan matches the user's original request."""
    builder = types.MetricPromptBuilder(
        metric_definition=(
            "Evaluate whether a proposed marathon plan matches the user's original intent. "
            "Check city match, date/season match, theme match, scale match, and budget goals."
        ),
        criteria={
            "City Match": "The plan takes place in the city the user requested.",
            "Date/Season Match": "The plan respects the user's date or season preferences.",
            "Theme Match": "The plan matches the user's desired theme (scenic, fast, charity, etc.).",
            "Scale Match": "The plan's scale matches what the user envisioned.",
            "Budget Goal Match": "The plan aligns with the user's budget objectives.",
        },
        rating_scores={
            "1": "Completely misaligned - Wrong city, wrong date, wrong theme",
            "25": "Mostly misaligned - Major elements don't match user intent",
            "50": "Partially aligned - Some elements match but key requirements missed",
            "75": "Mostly aligned - Minor deviations from user intent",
            "100": "Perfectly aligned - All user requirements addressed",
        },
    )

    return types.LLMMetric(
        name="intent_alignment",
        prompt_template=str(builder),
        judge_model=_get_model_resource(),
    )


def _check_distance_compliance_logic(response_text: str) -> dict:
    """Deterministic check for 26.2 mile (42.195 km) marathon distance."""
    text_lower = response_text.lower()

    score = 100.0
    issues = []

    mile_pattern = r'(\d+(?:\.\d+)?)\s*(?:miles?|mi)\b'
    km_pattern = r'(\d+(?:\.\d+)?)\s*(?:kilometers?|km)\b'

    mile_matches = re.findall(mile_pattern, text_lower)
    km_matches = re.findall(km_pattern, text_lower)

    for distance_str in mile_matches:
        distance = float(distance_str)
        if 20 <= distance <= 30:
            deviation = abs(distance - 26.2)
            if deviation > 0.5:
                score = 1.0
                issues.append(
                    f"Route distance {distance} miles deviates from "
                    f"26.2 mile standard by {deviation:.1f} miles"
                )
            elif deviation > 0.1:
                score = 60.0
                issues.append(
                    f"Route distance {distance} miles is close but not "
                    f"exactly 26.2 miles (deviation: {deviation:.2f} miles)"
                )

    for distance_str in km_matches:
        distance = float(distance_str)
        if 35 <= distance <= 50:
            deviation = abs(distance - 42.195)
            if deviation > 1.0:
                score = 1.0
                issues.append(
                    f"Route distance {distance} km deviates from "
                    f"42.195 km standard by {deviation:.1f} km"
                )
            elif deviation > 0.2:
                score = 60.0
                issues.append(
                    f"Route distance {distance} km is close but not "
                    f"exactly 42.195 km (deviation: {deviation:.2f} km)"
                )

    bypass_phrases = [
        "skip the distance", "doesn't need to be 26.2",
        "shorter route", "longer route",
        "half marathon", "ultra marathon", "10k", "5k route",
    ]
    for phrase in bypass_phrases:
        if phrase in text_lower:
            score = 1.0
            issues.append(f"Plan appears to bypass marathon distance: '{phrase}'")

    explanation = "; ".join(issues) if issues else "No distance issues detected"
    return {"score": score, "explanation": explanation}


def _create_distance_compliance_metric() -> types.Metric:
    """Deterministic check for 26.2 mile (42.195 km) marathon distance."""

    def check_distance_compliance(instance: dict) -> dict:
        response_text = instance["response"]["parts"][0]["text"]
        return _check_distance_compliance_logic(response_text)
    return types.Metric(
        name="distance_compliance",
        custom_function=check_distance_compliance,
    )


async def _run_custom_eval(
    project_id: str,
    location: str,
    user_intent: str,
    proposed_plan: str,
) -> tuple[dict[str, float], dict[str, str]]:
    """Run Vertex AI Evaluation with custom metrics."""
    vertexai.init(project=project_id, location=location)
    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=genai_types.HttpOptions(api_version="v1beta1"),
    )

    df = pd.DataFrame({
        "prompt": [user_intent],
        "response": [proposed_plan],
    })

    metrics = [
        _create_safety_compliance_metric(),
        _create_community_impact_metric(),
        _create_logistics_completeness_metric(),
        _create_financial_viability_metric(),
        _create_participant_experience_metric(),
        _create_intent_alignment_metric(),
        _create_distance_compliance_metric(),
    ]

    result = client.evals.evaluate(
        dataset=df,
        metrics=metrics,
    )

    scores = {}
    details = {}

    for case in result.eval_case_results:
        for cand in case.response_candidate_results:
            for metric_name, metric_result in cand.metric_results.items():
                raw_score = 50.0
                if hasattr(metric_result, "score") and metric_result.score is not None:
                    raw_score = metric_result.score

                normalized_score = float(raw_score)
                scores[metric_name] = round(normalized_score, 2)

                if hasattr(metric_result, "explanation") and metric_result.explanation:
                    details[metric_name] = metric_result.explanation

    return scores, details


def _heuristic_eval(
    user_intent: str,
    proposed_plan: str,
) -> tuple[dict[str, float], dict[str, str]]:
    """Heuristic evaluation when Vertex AI Eval is unavailable."""
    plan_lower = proposed_plan.lower()
    intent_lower = user_intent.lower()
    scores = {}
    details = {}

    # Safety compliance
    safety_score = 80.0
    safety_issues = []
    if "hospital" in plan_lower and "block" in plan_lower:
        safety_score = 30.0
        safety_issues.append("Route may block hospital access")
    if "emergency" in plan_lower and "no detour" in plan_lower:
        safety_score = 20.0
        safety_issues.append("No emergency detour specified")
    if any(kw in plan_lower for kw in ["emergency vehicle"]):
        safety_score = min(safety_score + 10.0, 100.0)
    scores["safety_compliance"] = safety_score
    details["safety_compliance"] = "; ".join(safety_issues) if safety_issues else "No safety issues detected"

    # Community impact
    community_score = 75.0
    community_issues = []
    bias_terms = ["only wealthy", "exclusive area", "avoid poor", "no access for"]
    for term in bias_terms:
        if term in plan_lower:
            community_score = 30.0
            community_issues.append(f"Equity concern: '{term}'")
    if any(kw in plan_lower for kw in ["cheer zone", "community", "resident"]):
        community_score = min(community_score + 10.0, 100.0)
    scores["community_impact"] = community_score
    details["community_impact"] = "; ".join(community_issues) if community_issues else "No community issues detected"

    # Logistics completeness
    logistics_score = 60.0
    logistics_issues = []
    if "hydration" in plan_lower or "nutrition" in plan_lower:
        logistics_score += 15.0
    if any(kw in plan_lower for kw in ["timing", "chip"]):
        logistics_score += 10.0
    if any(kw in plan_lower for kw in ["marshal", "course marshal"]):
        logistics_score += 10.0
    logistics_score = min(logistics_score, 100.0)
    if logistics_score < 70.0:
        logistics_issues.append("Logistics details appear incomplete")
    scores["logistics_completeness"] = logistics_score
    details["logistics_completeness"] = "; ".join(logistics_issues) if logistics_issues else "Logistics appear adequate"

    # Financial viability
    financial_score = 65.0
    financial_issues = []
    if any(kw in plan_lower for kw in ["budget", "cost", "revenue", "registration fee"]):
        financial_score += 15.0
    if any(kw in plan_lower for kw in ["sponsor", "sponsorship"]):
        financial_score += 10.0
    financial_score = min(financial_score, 100.0)
    if financial_score < 70.0:
        financial_issues.append("Financial plan lacks detail")
    scores["financial_viability"] = financial_score
    details["financial_viability"] = "; ".join(financial_issues) if financial_issues else "Financial plan appears sound"

    # Participant experience
    experience_score = 70.0
    experience_issues = []
    if any(kw in plan_lower for kw in ["scenic", "landmark", "view", "beautiful"]):
        experience_score += 15.0
    if any(kw in plan_lower for kw in ["medal", "post-race", "recovery", "food"]):
        experience_score += 10.0
    experience_score = min(experience_score, 100.0)
    scores["participant_experience"] = experience_score
    details["participant_experience"] = "; ".join(experience_issues) if experience_issues else "Experience appears good"

    # Intent alignment
    intent_score = 70.0
    intent_issues = []
    
    # Extract significant keywords (longer than 3 chars) from intent to check if they exist in the plan
    intent_words = [w for w in re.findall(r'\b\w+\b', intent_lower) if len(w) > 3]
    missing_themes = []
    
    # Check for basic theme/keyword alignment without hardcoded lists
    for word in intent_words:
        if word in ["marathon", "plan", "route", "with", "that", "this", "need"]:
            continue # skip common stop words
        if word not in plan_lower:
            missing_themes.append(word)
            
    if missing_themes:
        # Penalize slightly for missing intent keywords, but don't fail completely
        # as the LLM might use synonyms
        intent_score = max(40.0, intent_score - (len(missing_themes) * 10.0))
        if len(missing_themes) > 3:
            intent_issues.append(f"Plan may miss key user requirements: {', '.join(missing_themes[:3])}...")
        else:
            intent_issues.append(f"Plan may miss key user requirements: {', '.join(missing_themes)}")
    else:
        intent_score = 90.0

    scores["intent_alignment"] = intent_score
    details["intent_alignment"] = "; ".join(intent_issues) if intent_issues else "Plan appears aligned with intent"

    # Distance compliance (Reuse deterministic logic)
    distance_result = _check_distance_compliance_logic(proposed_plan)
    # Normalize score from 1-5 scale to 0.0-1.0 scale for the heuristic dictionary
    scores["distance_compliance"] = float(distance_result["score"])
    details["distance_compliance"] = distance_result["explanation"]

    return scores, details


# ============================================================================
# RESULT BUILDER
# ============================================================================


def _build_result(
    scores: dict[str, float],
    details: dict[str, str],
    eval_method: str,
) -> dict[str, Any]:
    """Build the final evaluation result from scores and details."""
    findings = []
    improvement_suggestions = []

    for criterion, score in scores.items():
        if score < 80.0:
            if score < SEVERITY_THRESHOLDS["high"]:
                severity = "high"
            elif score < SEVERITY_THRESHOLDS["medium"]:
                severity = "medium"
            else:
                severity = "low"

            findings.append({
                "criterion": criterion,
                "description": details.get(criterion, f"Score below threshold: {score}"),
                "severity": severity,
            })

            suggestion = _suggest_improvement(criterion, score, details.get(criterion, ""))
            if suggestion:
                improvement_suggestions.append(suggestion)

    overall_score = 0.0
    for criterion, weight in CRITERION_WEIGHTS.items():
        overall_score += scores.get(criterion, 50.0) * weight
    overall_score = round(overall_score, 2)

    passed = overall_score >= 85.0 and not any(
        f["severity"] == "high" for f in findings
    )

    return {
        "passed": passed,
        "scores": scores,
        "findings": findings,
        "improvement_suggestions": improvement_suggestions,
        "overall_score": overall_score,
        "eval_method": eval_method,
    }


def _suggest_improvement(criterion: str, score: float, detail: str) -> str:
    """Generate an actionable improvement suggestion for a criterion."""
    suggestions = {
        "safety_compliance": "Add emergency vehicle crossing points every 2 miles and plan detour routes around hospitals and fire stations.",
        "community_impact": "Include community engagement plans like cheer zones, notify affected residents, and ensure equitable route distribution.",
        "logistics_completeness": "Add timing chip details, plan course marshal positions, and detail start/finish infrastructure.",
        "financial_viability": "Add budget breakdown with cost estimates, identify 3+ revenue sources (registration, sponsors, merchandise), and project break-even participant count.",
        "participant_experience": "Highlight scenic landmarks along the route, plan spectator viewing areas, and detail post-race amenities (medals, food, recovery).",
        "intent_alignment": "Review the user's original request and ensure the plan matches their stated city, theme, scale, and budget goals.",
        "distance_compliance": "Verify the route is exactly 26.2 miles (42.195 km) for marathon certification.",
    }
    return suggestions.get(criterion, f"Improve {criterion} (current score: {score:.2f})")
