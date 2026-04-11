#!/usr/bin/env python3
"""CLI script for projecting marathon revenue.

Usage:
    python project_revenue.py --city "Las Vegas" --participants 30000 --fee 175 --year 1
"""

import argparse
import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[5]))
from src.economic_planner_agent.agent.tools import project_marathon_revenue


def main():
    parser = argparse.ArgumentParser(description="Project marathon revenue")
    parser.add_argument("--city", required=True, help="City name")
    parser.add_argument("--participants", type=int, required=True, help="Participant count")
    parser.add_argument("--fee", type=float, default=150.0, help="Registration fee USD")
    parser.add_argument("--year", type=int, default=1, help="Event year (1=inaugural)")
    args = parser.parse_args()

    result = project_marathon_revenue(
        city=args.city,
        participant_count=args.participants,
        registration_fee_usd=args.fee,
        event_year=args.year,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
