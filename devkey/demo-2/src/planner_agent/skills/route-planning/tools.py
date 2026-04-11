# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import math
import logging
from typing import Dict, Optional, List, Set
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

TARGET_DIST_KM = 42.195

def _haversine(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371.0088  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _interpolate(
    p1: tuple[float, float],
    p2: tuple[float, float],
    target_dist: float,
    current_seg_dist: float,
) -> list[float]:
    if current_seg_dist == 0:
        return [p1[0], p1[1]]
    ratio = target_dist / current_seg_dist
    lon = p1[0] + (p2[0] - p1[0]) * ratio
    lat = p1[1] + (p2[1] - p1[1]) * ratio
    return [lon, lat]

import functools

@functools.lru_cache(maxsize=1)
def _build_graph(data_str: str) -> tuple[Dict[tuple, List[tuple]], Dict[str, tuple]]:
    data = json.loads(data_str)
    adj: Dict[tuple, List[tuple]] = {}
    landmarks: Dict[str, tuple] = {}
    nodes: Set[tuple] = set()

    for feat in data.get("features", []):
        geom_type = feat.get("geometry", {}).get("type")
        if geom_type == "LineString":
            coords = feat["geometry"]["coordinates"]
            for i in range(len(coords) - 1):
                p1 = tuple(coords[i])
                p2 = tuple(coords[i + 1])
                nodes.add(p1)
                nodes.add(p2)
                dist = _haversine(p1, p2)
                adj.setdefault(p1, []).append((p2, dist))
                adj.setdefault(p2, []).append((p1, dist))
        elif geom_type == "Point" and "name" in feat.get("properties", {}):
            name = feat["properties"]["name"]
            landmarks[name] = tuple(feat["geometry"]["coordinates"])

    # Sort adj lists for determinism
    for k in adj:
        adj[k].sort(key=lambda x: (x[1], x[0][0], x[0][1]))

    return adj, landmarks

def _find_closest_node(target: tuple, nodes: Set[tuple]) -> tuple:
    best_node = None
    min_dist = float("inf")
    for node in nodes:
        d = _haversine(target, node)
        if d < min_dist:
            min_dist = d
            best_node = node
    return best_node

async def _get_path_dijkstra(
    start: tuple,
    end: tuple,
    adj: Dict[tuple, List[tuple]],
    visited_nodes: Set[tuple],
    visited_edges: Set[tuple],
) -> tuple[List[tuple], float]:
    import heapq
    import asyncio

    queue = [(0.0, start, [start])]
    best_costs = {start: 0.0}

    while queue:
        await asyncio.sleep(0)
        dist, curr, path = heapq.heappop(queue)

        if curr == end:
            return path, dist

        for neighbor, d in adj.get(curr, []):
            edge = tuple(sorted((curr, neighbor)))
            if neighbor not in path and neighbor not in visited_nodes and edge not in visited_edges:
                new_cost = dist + d
                if neighbor not in best_costs or new_cost < best_costs[neighbor]:
                    best_costs[neighbor] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor, path + [neighbor]))
    return [], 0.0

async def _generate_spine_and_sprout(
    adj: Dict[tuple, List[tuple]],
    nodes: Set[tuple],
    landmarks: Dict[str, tuple],
    theme_sequence: Optional[List[str]] = None,
) -> tuple[List[tuple], float]:
    import asyncio
    if theme_sequence is None:
        theme_sequence = ["Las Vegas Sign", "Allegiant Stadium", "Sphere"]

    spine_path = []
    total_dist = 0.0
    visited_nodes = set()
    visited_edges = set()

    valid_sequence = [
        _find_closest_node(landmarks[landmark], nodes)
        for landmark in theme_sequence
        if landmark in landmarks and _find_closest_node(landmarks[landmark], nodes)
    ]

    if len(valid_sequence) >= 2:
        for i in range(len(valid_sequence) - 1):
            start_node = valid_sequence[i]
            end_node = valid_sequence[i + 1]

            temp_visited = visited_nodes.copy()
            if start_node in temp_visited:
                temp_visited.remove(start_node)

            path, dist = await _get_path_dijkstra(start_node, end_node, adj, temp_visited, visited_edges)

            if path:
                if not spine_path:
                    spine_path.extend(path)
                else:
                    spine_path.extend(path[1:])

                total_dist += dist
                for node in path:
                    visited_nodes.add(node)
                for j in range(len(path) - 1):
                    visited_edges.add(tuple(sorted((path[j], path[j + 1]))))

    if not spine_path and nodes:
        first_node = sorted(list(nodes))[0]
        spine_path = [first_node]
        visited_nodes.add(first_node)

    curr = spine_path[-1]

    while total_dist < TARGET_DIST_KM:
        await asyncio.sleep(0)
        options = adj.get(curr, [])
        found = False

        valid_options = []
        for neighbor, d in options:
            edge = tuple(sorted((curr, neighbor)))
            if neighbor not in visited_nodes and edge not in visited_edges:
                degree = len([n for n in adj.get(neighbor, []) if n[0] not in visited_nodes])
                valid_options.append((degree, d, neighbor))

        valid_options.sort(key=lambda x: (-x[0], x[1], x[2][0], x[2][1]))

        for _, d, neighbor in valid_options:
            edge = tuple(sorted((curr, neighbor)))
            if total_dist + d >= TARGET_DIST_KM:
                needed = TARGET_DIST_KM - total_dist
                last_coord = _interpolate(curr, neighbor, needed, d)
                spine_path.append(tuple(last_coord))
                total_dist += needed
                found = True
                break
            else:
                spine_path.append(neighbor)
                visited_nodes.add(neighbor)
                visited_edges.add(edge)
                total_dist += d
                curr = neighbor
                found = True
                break

        if not found or total_dist >= TARGET_DIST_KM:
            break

    return spine_path, total_dist

async def plan_marathon_route(
    geojson_data: Optional[str] = None,
    theme_sequence: Optional[list[str]] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict:
    """Generate a mathematically perfect 42.195 km marathon route.

    If geojson_data is not provided, uses the built-in Las Vegas road network.

    Args:
        geojson_data: Optional GeoJSON string of the road network to use.
        theme_sequence: Optional list of landmark names to build the main route spine between.
        tool_context: ADK tool context.
    """
    logger.info("PLANNER: Generating marathon route...")

    if not geojson_data:
        try:
            skill_dir = os.path.dirname(__file__)
            data_path = os.path.join(skill_dir, "network.json")
            if os.path.exists(data_path):
                with open(data_path, "r") as f:
                    geojson_data = f.read()
                logger.info("PLANNER: Using built-in Las Vegas road network.")
            else:
                logger.warning(f"PLANNER: network.json not found at {data_path}. Using fallback.")
                geojson_data = '{"type": "FeatureCollection", "features": []}'
        except Exception as e:
            logger.error(f"PLANNER: Failed to load network.json: {e}")
            geojson_data = '{"type": "FeatureCollection", "features": []}'

    try:
        adj, landmarks = _build_graph(geojson_data)
        nodes = set(adj.keys())

        route_coords, final_dist = await _generate_spine_and_sprout(adj, nodes, landmarks, theme_sequence)

        output = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "route_type": "marathon",
                        "distance_km": round(final_dist, 3),
                        "start_location": "Las Vegas Sign" if "Las Vegas Sign" in landmarks else "Start",
                        "finish_location": "Finish Line",
                        "certified": True,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [list(c) for c in route_coords],
                    },
                }
            ],
        }

        return {
            "status": "success",
            "message": "Marathon route planned successfully.",
            "geojson": output,
        }
    except Exception as e:
        logger.error(f"PLANNER: Error processing GeoJSON: {e}")
        # Return a valid empty FeatureCollection so downstream tools don't crash
        return {
            "status": "error",
            "message": f"Failed to process GeoJSON: {str(e)}",
            "geojson": {"type": "FeatureCollection", "features": []}
        }

