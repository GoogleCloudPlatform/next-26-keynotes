#!/usr/bin/env python3
"""Analyze demographic inclusivity of a marathon route.

Usage:
    python analyze_demographics.py --waypoints "Fremont Street,Bellagio,UNLV Campus"
"""

import argparse
import json


NEIGHBORHOODS = {
    "downtown": {"name": "Downtown Las Vegas", "population": 45000, "median_income": 42000, "diversity_index": 0.72, "landmarks": ["fremont street", "container park", "arts district"]},
    "the_strip": {"name": "The Strip Corridor", "population": 12000, "median_income": 55000, "diversity_index": 0.65, "landmarks": ["bellagio", "caesars palace", "mgm grand"]},
    "east_las_vegas": {"name": "East Las Vegas", "population": 85000, "median_income": 35000, "diversity_index": 0.85, "landmarks": ["wetlands park", "sunrise hospital", "boulder highway"]},
    "summerlin": {"name": "Summerlin", "population": 110000, "median_income": 85000, "diversity_index": 0.55, "landmarks": ["red rock canyon", "downtown summerlin"]},
    "north_las_vegas": {"name": "North Las Vegas", "population": 95000, "median_income": 38000, "diversity_index": 0.82, "landmarks": ["craig ranch park", "aliante casino"]},
    "unlv_area": {"name": "UNLV / Maryland Parkway", "population": 55000, "median_income": 32000, "diversity_index": 0.78, "landmarks": ["unlv campus", "thomas & mack center"]},
    "historic_westside": {"name": "Historic Westside", "population": 25000, "median_income": 28000, "diversity_index": 0.88, "landmarks": ["moulin rouge site", "martin luther king"]},
}


def analyze(waypoints: list[str]) -> dict:
    if len(waypoints) < 2:
        return {"error": "At least 2 waypoints required.", "inclusivity_grade": "F"}

    touched = []
    for wp in waypoints:
        wp_lower = wp.lower()
        for nid, data in NEIGHBORHOODS.items():
            if any(lm in wp_lower or wp_lower in lm for lm in data["landmarks"]) or nid in wp_lower:
                if data["name"] not in touched:
                    touched.append(data["name"])

    if not touched:
        touched = ["Downtown Las Vegas", "The Strip Corridor"]

    touched_data = [d for d in NEIGHBORHOODS.values() if d["name"] in touched]
    diversities = [d["diversity_index"] for d in touched_data]
    diversity_score = round(sum(diversities) / len(diversities), 2) if diversities else 0
    coverage = len(touched) / len(NEIGHBORHOODS)

    median_income = 42000
    underserved = [d["name"] for d in NEIGHBORHOODS.values() if d["median_income"] < median_income]
    underserved_touched = [n for n in touched if n in underserved]
    underserved_pct = len(underserved_touched) / len(underserved) * 100 if underserved else 0

    combined = (diversity_score * 0.4) + (coverage * 0.3) + (underserved_pct / 100 * 0.3)
    grade = "A" if combined >= 0.7 else "B" if combined >= 0.55 else "C" if combined >= 0.4 else "D" if combined >= 0.25 else "F"

    return {
        "neighborhoods_touched": touched,
        "diversity_score": diversity_score,
        "inclusivity_grade": grade,
        "underserved_coverage_percent": round(underserved_pct, 1),
        "coverage_ratio": round(coverage, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze route demographic inclusivity")
    parser.add_argument("--waypoints", required=True, help="Comma-separated waypoints")
    args = parser.parse_args()
    waypoints = [w.strip() for w in args.waypoints.split(",")]
    result = analyze(waypoints)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
