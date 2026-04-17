"""Script to check marathon plan readiness for simulation.

Used by the review-marathon-plan skill.
"""

import re


def check_readiness(plan_text: str) -> dict:
    """Check a marathon plan for simulation readiness.

    Args:
        plan_text: The full text of the marathon plan.

    Returns:
        dict with readiness assessment.
    """
    plan_lower = plan_text.lower()

    checks = {
        "has_distance": False,
        "has_waypoints": any(kw in plan_lower for kw in ["waypoint", "landmark"]),
        "has_timing": any(kw in plan_lower for kw in ["timing", "chip"]),
        "has_emergency_plan": any(kw in plan_lower for kw in ["emergency", "evacuation"]),
        "has_budget": any(kw in plan_lower for kw in ["budget", "cost", "revenue"]),
        "has_schedule": any(kw in plan_lower for kw in ["schedule", "timeline", "race day"]),
    }

    # Check distance presence (not value)
    mile_pattern = r"(\d+(?:\.\d+)?)\s*(?:miles?|mi)\b"
    km_pattern = r"(\d+(?:\.\d+)?)\s*(?:kilometers?|km)\b"
    if re.search(mile_pattern, plan_lower) or re.search(km_pattern, plan_lower):
        checks["has_distance"] = True

    passed = sum(checks.values())
    total = len(checks)

    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "score": round(passed / total, 2),
        "ready": passed >= (total - 1),  # Allow one minor missing element
    }
