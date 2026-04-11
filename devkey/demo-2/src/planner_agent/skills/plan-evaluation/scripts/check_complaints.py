#!/usr/bin/env python3
"""Check nuisance complaint density for a Las Vegas neighborhood.

Usage:
    python check_complaints.py --neighborhood "downtown"
"""

import argparse
import json
import random


NEIGHBORHOODS = {
    "downtown": {"name": "Downtown Las Vegas", "population": 45000, "median_age": 38, "density": "high"},
    "the_strip": {"name": "The Strip Corridor", "population": 12000, "median_age": 34, "density": "low"},
    "east_las_vegas": {"name": "East Las Vegas", "population": 85000, "median_age": 32, "density": "high"},
    "summerlin": {"name": "Summerlin", "population": 110000, "median_age": 42, "density": "medium"},
    "north_las_vegas": {"name": "North Las Vegas", "population": 95000, "median_age": 30, "density": "high"},
    "henderson": {"name": "Henderson", "population": 120000, "median_age": 44, "density": "medium"},
    "unlv_area": {"name": "UNLV / Maryland Parkway", "population": 55000, "median_age": 26, "density": "high"},
    "spring_valley": {"name": "Spring Valley", "population": 90000, "median_age": 36, "density": "high"},
    "arts_district": {"name": "18b Arts District", "population": 8000, "median_age": 33, "density": "medium"},
    "historic_westside": {"name": "Historic Westside", "population": 25000, "median_age": 35, "density": "high"},
}


def check_complaints(neighborhood_id: str) -> dict:
    nid = neighborhood_id.lower().replace(" ", "_").replace("-", "_")

    neighborhood = None
    for key, data in NEIGHBORHOODS.items():
        if key == nid or nid in key or key in nid:
            neighborhood = data
            break

    if not neighborhood:
        return {"error": f"Neighborhood '{neighborhood_id}' not found.", "available": list(NEIGHBORHOODS.keys())}

    density_factor = {"low": 0.5, "medium": 1.0, "high": 1.8}[neighborhood["density"]]
    base = int(neighborhood["population"] * 0.02 * density_factor)

    if density_factor > 1.5 and neighborhood["median_age"] > 35:
        sensitivity = "critical"
    elif density_factor > 1:
        sensitivity = "high"
    elif density_factor > 0.7:
        sensitivity = "medium"
    else:
        sensitivity = "low"

    return {
        "neighborhood": neighborhood["name"],
        "sensitivity_rating": sensitivity,
        "estimated_complaints": base,
        "density": neighborhood["density"],
        "population": neighborhood["population"],
    }


def main():
    parser = argparse.ArgumentParser(description="Check neighborhood complaint density")
    parser.add_argument("--neighborhood", required=True, help="Neighborhood ID")
    args = parser.parse_args()
    result = check_complaints(args.neighborhood)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
