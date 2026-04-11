#!/usr/bin/env python3
"""CLI script for estimating local business impact.

Usage:
    python estimate_impact.py --city "Las Vegas" --participants 30000 --days 3
"""

import argparse
import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[5]))
from src.economic_planner_agent.agent.tools import estimate_local_business_impact


def main():
    parser = argparse.ArgumentParser(description="Estimate local business impact")
    parser.add_argument("--city", required=True, help="City name")
    parser.add_argument("--participants", type=int, required=True, help="Participant count")
    parser.add_argument("--days", type=int, default=3, help="Event duration in days")
    args = parser.parse_args()

    result = estimate_local_business_impact(
        city=args.city,
        participant_count=args.participants,
        event_duration_days=args.days,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
