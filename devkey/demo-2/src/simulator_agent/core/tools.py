"""Tools for the Simulation Controller Agent.

Provides tools for reviewing marathon plan readiness.
"""

import re
from typing import Any


async def check_plan_readiness(
    plan_text: str,
) -> dict[str, Any]:
    """Check a marathon plan for simulation readiness.

    Performs deterministic checks on the plan text to identify
    missing elements and assess completeness.

    Args:
        plan_text: The full text of the marathon plan to review.

    Returns:
        dict with readiness assessment including checklist results,
        missing elements, and a readiness score.
    """
    plan_lower = plan_text.lower()

    checklist = {
        "distance_specified": False,
        "water_stations": False,
        "medical_tents": False,
        "timing_system": False,
        "start_finish": False,
        "emergency_access": False,
        "budget_included": False,
        "timeline_included": False,
    }

    # Distance check - just check for ANY distance mention, don't validate the value
    mile_pattern = r'(\d+(?:\.\d+)?)\s*(?:miles?|mi)\b'
    km_pattern = r'(\d+(?:\.\d+)?)\s*(?:kilometers?|km)\b'
    if re.search(mile_pattern, plan_lower) or re.search(km_pattern, plan_lower):
        checklist["distance_specified"] = True

    # Logistics checks - presence of keywords
    if "water station" in plan_lower:
        checklist["water_stations"] = True
    if any(kw in plan_lower for kw in ["medical tent", "first aid", "medical station"]):
        checklist["medical_tents"] = True
    if any(kw in plan_lower for kw in ["timing", "chip", "tracking"]):
        checklist["timing_system"] = True
    if any(kw in plan_lower for kw in ["start line", "finish line", "start/finish", "starting area"]):
        checklist["start_finish"] = True
    if any(kw in plan_lower for kw in ["emergency", "ambulance", "evacuation"]):
        checklist["emergency_access"] = True
    if any(kw in plan_lower for kw in ["budget", "cost", "revenue", "expense"]):
        checklist["budget_included"] = True
    if any(kw in plan_lower for kw in ["schedule", "timeline", "race day", "setup"]):
        checklist["timeline_included"] = True

    passed = sum(checklist.values())
    total = len(checklist)
    score = passed / total

    missing = [k for k, v in checklist.items() if not v]

    return {
        "checklist": checklist,
        "missing_elements": missing,
        "readiness_score": round(score, 2),
        "passed_checks": passed,
        "total_checks": total,
    }


def get_tools() -> list:
    """Return the FunctionTools for this agent.

    Returns:
        List of callable tools for this agent.
    """
    return [
        check_plan_readiness,
    ]
