# Evaluation Criteria Reference

## Scoring Criteria and Weights

| Criterion | Weight | What It Measures |
|---|---|---|
| Safety Compliance | 0.20 | Emergency plans, medical coverage, course safety, crowd management |
| Community Impact | 0.15 | Resident consideration, noise mitigation, inclusivity, engagement |
| Logistics Completeness | 0.20 | Water stations, medical tents, timing systems, volunteers, equipment |
| Financial Viability | 0.15 | Budget balance, diverse revenue sources, cost management, sponsorship |
| Participant Experience | 0.15 | Course quality, amenities, spectator areas, runner services |
| Intent Alignment | 0.10 | How well the plan matches the user's specific request and constraints |
| Distance Compliance | 0.05 | Whether the route totals exactly 26.2 miles (deterministic check) |

## Passing Threshold

- **Pass**: overall_score >= 0.85
- **Fail**: overall_score < 0.85

## Common Issues by Criterion

### Safety Compliance (Low Score Fixes)
- Add explicit emergency vehicle access plan
- Include medical tent locations (every 5 miles + finish)
- Describe crowd management strategy for start/finish
- Add weather contingency plan

### Community Impact (Low Score Fixes)
- Address noise concerns for residential areas
- Add cheer zone locations with community activities
- Include ADA accessibility plan
- Describe resident notification process

### Logistics Completeness (Low Score Fixes)
- Ensure 20+ water stations for full marathon
- Add timing mat locations (start, 5K, 10K, half, 30K, finish)
- Include volunteer count and roles
- Describe course marshal deployment

### Financial Viability (Low Score Fixes)
- Show revenue-cost balance
- Include multiple revenue sources (registration, sponsorship, merchandise)
- Add sponsorship tier structure
- Provide cost breakdown by category

### Participant Experience (Low Score Fixes)
- Add spectator viewing areas
- Include entertainment along the route
- Describe post-race amenities (food, massage, photos)
- Add pace group support

### Intent Alignment (Low Score Fixes)
- Re-read the original user request
- Ensure all specified requirements are addressed
- Match the requested theme, city, scale, and budget goal
- If constraints conflict, explain the trade-offs

### Distance Compliance (Low Score Fixes)
- Calculate route distance from waypoints
- Adjust waypoints to hit exactly 26.2 miles
- Note: this is a deterministic check, not LLM-judged
