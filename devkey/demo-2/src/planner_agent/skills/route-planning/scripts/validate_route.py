"""Validate a marathon route for distance and waypoint completeness."""


def validate_route(
    waypoints: list[str],
    distance_miles: float,
) -> dict:
    """Validate a marathon route meets certification requirements.

    Args:
        waypoints: Ordered list of route waypoints
        distance_miles: Total route distance in miles

    Returns:
        dict with validation results and recommendations
    """
    issues = []
    warnings = []

    # Distance validation
    if abs(distance_miles - 26.2) > 0.5:
        issues.append(
            f"Distance {distance_miles:.1f} miles is not close to 26.2 miles. "
            "A certified marathon must be exactly 26.2 miles."
        )
    elif abs(distance_miles - 26.2) > 0.1:
        warnings.append(
            f"Distance {distance_miles:.1f} miles is close but not exact. "
            "Target exactly 26.2 miles for certification."
        )

    # Waypoint validation
    if len(waypoints) < 3:
        issues.append(
            f"Only {len(waypoints)} waypoints. Need at least 3 "
            "(start, intermediate, finish) for a valid route."
        )
    elif len(waypoints) < 8:
        warnings.append(
            f"Only {len(waypoints)} waypoints. Consider 8-15 for a "
            "well-defined marathon route."
        )

    passed = len(issues) == 0

    return {
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
        "waypoint_count": len(waypoints),
        "distance_miles": distance_miles,
    }
