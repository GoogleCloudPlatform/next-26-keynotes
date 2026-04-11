---
name: review-marathon-plan
description: Step-by-step methodology for reviewing marathon plans for simulation readiness, covering route feasibility, logistics completeness, and safety clearance.
---

# Review Marathon Plan

## Purpose

Systematically confirm that a marathon plan is ready for simulation execution by verifying the presence of all required prerequisite data.

## Procedure

### Step 1: Prerequisite Data Verification

Use the `check_plan_readiness` tool to confirm the presence of the following sections:

1. **Route Data**: Waypoints, landmarks, distance (26.2 mi / 42.195 km), and start/finish locations.
2. **Logistics Data**: Water stations, medical tents, timing systems, and participant scale.
3. **Safety Data**: Emergency access routes, evacuation plans, and crowd management.

### Step 2: Approval Decision

1. Set `approved=true` ONLY if all three data categories (Route, Logistics, Safety) are present and accounted for.
2. If any critical data is missing, set `approved=false` and list the missing elements in `blockers`.
3. Provide `recommendations` for any minor data gaps or clarifications needed for a better simulation.
