---
name: route-planning
description:
  Generates high-fidelity marathon routes using road network data (Dijkstra's algorithm)
  and outputting GeoJSON for visualization.
---

# Route Planning Skill

**Goal:** Design a mathematically perfect 42.195 km marathon route using real road network data, ensuring distance certification.

## Capabilities

- **Automated Route Generation**: Uses a built-in road network (`network.json`) and Dijkstra's algorithm to calculate a certified 42.195 km route between specified landmarks.
- **GeoJSON Output**: Returns a standards-compliant GeoJSON FeatureCollection that the UI uses to emit a `marathon_route_geojson` event for real-time map visualization.

## Resources

### Data
- `network.json`: Road network adjacency graph for Las Vegas.

### Tools (Python)
- `tools.py`: Contains the core `plan_marathon_route` implementation.

### Scripts
- `scripts/validate_route.py`: Validates distance and waypoints.

### References
- `references/marathon_planning_guide.md`: Consolidated guide for marathon standards, road width, traffic severity, and supported landmarks.
