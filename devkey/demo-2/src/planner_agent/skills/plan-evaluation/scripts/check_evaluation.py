"""Check evaluation results and determine next action."""


def check_evaluation(
    overall_score: float,
    passed: bool,
    iteration: int,
    max_iterations: int = 3,
) -> dict:
    """Check evaluation results and recommend next action.

    Args:
        overall_score: Overall evaluation score (0.0-1.0)
        passed: Whether the plan passed
        iteration: Current iteration number (1-based)
        max_iterations: Maximum allowed iterations

    Returns:
        dict with action recommendation and reasoning
    """
    if passed:
        return {
            "action": "present",
            "reason": f"Plan passed with score {overall_score:.2f} on iteration {iteration}.",
            "score": overall_score,
            "iteration": iteration,
        }

    if iteration >= max_iterations:
        return {
            "action": "present_with_caveats",
            "reason": (
                f"Maximum iterations ({max_iterations}) reached. "
                f"Best score: {overall_score:.2f}. Present with remaining issues noted."
            ),
            "score": overall_score,
            "iteration": iteration,
        }

    gap = 0.85 - overall_score
    if gap < 0.05:
        difficulty = "minor revisions needed"
    elif gap < 0.15:
        difficulty = "moderate revisions needed"
    else:
        difficulty = "significant revisions needed"

    return {
        "action": "revise",
        "reason": (
            f"Score {overall_score:.2f} below threshold 0.85 "
            f"(gap: {gap:.2f}). {difficulty.capitalize()}."
        ),
        "score": overall_score,
        "iteration": iteration,
        "gap": gap,
        "difficulty": difficulty,
    }
