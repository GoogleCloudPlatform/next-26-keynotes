---
name: review-marathon-plan
description: Step-by-step methodology for reviewing marathon plans for simulation readiness, covering route feasibility, logistics completeness, and safety clearance.
---

# Review Marathon Plan

## Purpose

Systematically review a marathon plan to determine if it is ready for simulation execution. This skill provides a structured review methodology covering route feasibility, logistics completeness, and safety clearance.

## Procedure

### Step 1: Route Feasibility Assessment

1. Verify the route distance is exactly 26.2 miles (42.195 km)
2. Check that waypoints are geographically plausible and form a connected path
3. Confirm start and finish locations are specified with adequate capacity
4. Assess elevation profile suitability for the event type
5. Verify the route passes through the landmarks/areas specified in requirements

**Score**: Rate route feasibility as `feasible`, `marginal`, or `infeasible`

### Step 2: Logistics Completeness Check

Use the `check_plan_readiness` tool to perform automated checks, then review:

1. **Water stations**: At least 20 for a full marathon (every 1-2 miles)
2. **Medical tents**: Positioned at key intervals and high-risk areas
3. **Timing systems**: Chip timing, mats, and tracking specified
4. **Course marshals**: Sufficient count for route length and complexity
5. **Start/finish infrastructure**: Corrals, stages, post-race amenities
6. **Equipment lists**: Barriers, signage, communication systems

**Score**: Rate logistics as `ready`, `partial`, or `not_ready`

### Step 3: Safety Clearance Review

1. Emergency vehicle access: Can ambulances reach any point on the route?
2. Hospital access: Are nearby hospitals accessible during the event?
3. Fire station access: Are fire stations accessible or detoured?
4. Evacuation routes: Are evacuation routes documented?
5. Crowd management: Is the plan adequate for expected participant count?
6. Weather contingency: Is there a plan for adverse weather?

**Score**: Rate safety as `cleared`, `conditional`, or `blocked`

### Step 4: Compile Approval Decision

1. Calculate `overall_readiness` as weighted average:
   - Route feasibility: 30%
   - Logistics readiness: 40%
   - Safety clearance: 30%
2. Identify `blockers` (critical issues that prevent approval)
3. Identify `recommendations` (non-critical improvements)
4. Set `approved` based on: no blockers AND overall_readiness >= 0.85
