"""Named demo scenarios for the Marathon Planner Agent.

Each scenario defines the prompt, agent configuration, and expected behavior
for a specific demo variant. The demo runner (`run.sh`) uses these to send
the right prompt to the right endpoint.

Two built-in scenarios:
- solo: Evaluator only, no Simulation Controller
- full_team: Evaluator + Simulation Controller for full approval flow
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scenario:
    """A named demo scenario configuration."""

    name: str
    description: str
    demo_prompt: str
    enabled_agents: list[str] = field(default_factory=list)
    expected_behavior: str = ""
    endpoint_suffix: str = ""


# ============================================================================
# DEMO PROMPT
# ============================================================================

# Shared base prompt
_DEMO_PROMPT = (
    "Plan a scenic marathon in Las Vegas for March 2026 with 15,000 participants. "
    "The route should pass by the Strip, Fremont Street, and the Arts District. "
    "Include a charity component benefiting local schools."
)

# ============================================================================
# SCENARIOS
# ============================================================================

SCENARIOS: dict[str, Scenario] = {
    "solo": Scenario(
        name="solo",
        description=(
            "Marathon Planner runs with Evaluator only (no Simulation Controller). "
            "The planner uses built-in skills for route, traffic, community, and "
            "economic analysis. The evaluator scores the plan and provides feedback "
            "for iterative improvement."
        ),
        demo_prompt=_DEMO_PROMPT,
        enabled_agents=["evaluator"],
        expected_behavior=(
            "1. Agent generates initial plan using consolidated skills\n"
            "2. Sends plan to Evaluator Agent via A2A for quality scoring\n"
            "3. If score < 0.85, revises based on evaluator feedback\n"
            "4. Iterates until plan passes evaluation\n"
            "5. Presents final plan (no simulation approval step)"
        ),
        endpoint_suffix="-solo",
    ),
    "full_team": Scenario(
        name="full_team",
        description=(
            "Marathon Planner runs with both Evaluator and Simulation Controller. "
            "After the plan passes evaluation, it is submitted to the Simulation "
            "Controller for formal approval before simulation execution."
        ),
        demo_prompt=_DEMO_PROMPT,
        enabled_agents=["evaluator", "simulation_controller"],
        expected_behavior=(
            "1. Agent generates comprehensive plan using all 13 skills\n"
            "2. Sends plan to Evaluator Agent via A2A for quality scoring\n"
            "3. If score < 0.85, revises based on evaluator feedback\n"
            "4. Once evaluation passes, sends to Simulation Controller via A2A\n"
            "5. Controller reviews route feasibility, logistics, safety\n"
            "6. Returns approval decision with readiness score\n"
            "7. Presents final approved plan with evaluation + approval results"
        ),
        endpoint_suffix="-full",
    ),
}
