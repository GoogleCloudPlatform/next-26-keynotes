"""Check venue capacity for marathon event infrastructure.

Usage:
    python check_capacity.py --location "Fremont Street Experience" \
        --event-type marathon_start_finish --attendance 5000

Outputs JSON with capacity assessment and recommendations.
"""

import argparse
import json
import random
import sys


# Venue capacity data
VENUE_CAPACITIES = {
    "Fremont Street Experience": {"area_sqm": 45000, "max_capacity": 25000},
    "Las Vegas Convention Center": {"area_sqm": 185000, "max_capacity": 80000},
    "Welcome to Las Vegas Sign": {"area_sqm": 2000, "max_capacity": 1500},
    "Bellagio Fountains": {"area_sqm": 8000, "max_capacity": 5000},
    "Caesars Palace": {"area_sqm": 15000, "max_capacity": 10000},
    "MGM Grand": {"area_sqm": 12000, "max_capacity": 8000},
    "Mandalay Bay": {"area_sqm": 18000, "max_capacity": 12000},
    "Sunset Park": {"area_sqm": 130000, "max_capacity": 30000},
    "Craig Ranch Regional Park": {"area_sqm": 95000, "max_capacity": 20000},
    "Springs Preserve": {"area_sqm": 72000, "max_capacity": 15000},
    "Symphony Park": {"area_sqm": 28000, "max_capacity": 12000},
    "Downtown Container Park": {"area_sqm": 5000, "max_capacity": 3000},
    "UNLV Campus": {"area_sqm": 65000, "max_capacity": 25000},
    "World Market Center": {"area_sqm": 45000, "max_capacity": 20000},
}

TYPE_MULTIPLIERS = {
    "marathon_start_finish": 1.0,
    "water_station": 0.15,
    "spectator_zone": 0.5,
    "staging_area": 0.3,
}


def check_capacity(
    location_name: str,
    event_type: str = "marathon_start_finish",
    expected_attendance: int = 5000,
) -> dict:
    """Check if a location has sufficient capacity."""
    multiplier = TYPE_MULTIPLIERS.get(event_type, 0.5)
    needed_capacity = int(expected_attendance * multiplier)

    # Find matching venue
    venue_data = None
    resolved_name = location_name
    for venue_name, data in VENUE_CAPACITIES.items():
        if (
            venue_name.lower() in location_name.lower()
            or location_name.lower() in venue_name.lower()
        ):
            venue_data = data
            resolved_name = venue_name
            break

    if not venue_data:
        venue_data = {
            "area_sqm": random.randint(5000, 30000),
            "max_capacity": random.randint(3000, 15000),
        }

    effective_capacity = venue_data["max_capacity"]
    sufficient = effective_capacity >= needed_capacity
    utilization = (
        round((needed_capacity / effective_capacity) * 100, 1)
        if effective_capacity > 0
        else 100
    )

    recommendations = []
    if utilization > 90:
        recommendations.append("Capacity is near maximum. Consider overflow areas.")
    if utilization > 100:
        recommendations.append(
            f"OVER CAPACITY by {needed_capacity - effective_capacity} people. "
            "Must find additional space or reduce attendance."
        )
    if event_type == "marathon_start_finish" and effective_capacity < 10000:
        recommendations.append(
            "Start/finish area should ideally hold 10,000+. Consider a larger venue."
        )
    if event_type == "water_station" and venue_data["area_sqm"] < 500:
        recommendations.append(
            "Water station area is small. Ensure adequate table setup space."
        )
    if sufficient and not recommendations:
        recommendations.append("Location meets capacity requirements.")

    return {
        "location": resolved_name,
        "event_type": event_type,
        "capacity": effective_capacity,
        "needed_capacity": needed_capacity,
        "sufficient": sufficient,
        "utilization_percent": utilization,
        "area_sq_meters": venue_data["area_sqm"],
        "expected_attendance": expected_attendance,
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check venue capacity")
    parser.add_argument("--location", type=str, required=True, help="Location name")
    parser.add_argument(
        "--event-type",
        type=str,
        default="marathon_start_finish",
        choices=list(TYPE_MULTIPLIERS.keys()),
        help="Event type",
    )
    parser.add_argument(
        "--attendance", type=int, default=5000, help="Expected attendance"
    )
    args = parser.parse_args()

    result = check_capacity(args.location, args.event_type, args.attendance)
    print(json.dumps(result, indent=2))
