#!/usr/bin/env python3
"""CLI script for analyzing sponsorship potential.

Usage:
    python analyze_sponsorship.py --city "Las Vegas" --participants 30000 --theme general
"""

import argparse
import json
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[5]))
from src.economic_planner_agent.agent.tools import analyze_sponsorship_potential


def main():
    parser = argparse.ArgumentParser(description="Analyze sponsorship potential")
    parser.add_argument("--city", required=True, help="City name")
    parser.add_argument("--participants", type=int, required=True, help="Participant count")
    parser.add_argument("--theme", default="general", help="Event theme")
    args = parser.parse_args()

    result = analyze_sponsorship_potential(
        city=args.city,
        participant_count=args.participants,
        event_theme=args.theme,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
