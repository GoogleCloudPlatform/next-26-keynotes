#!/usr/bin/env python3
"""Search community sentiment data for marathon planning.

Usage:
    python search_sentiment.py --query "noise complaints near residential areas"
"""

import argparse
import json


SENTIMENT_DATABASE = [
    {"source": "Town Hall Meeting - Downtown Residents Association (March 2025)", "sentiment": "mixed", "key_quote": "We support the marathon but need guaranteed emergency vehicle access on 4th Street.", "topics": ["access", "emergency", "downtown", "road closure"]},
    {"source": "Clark County Community Survey Q4 2025", "sentiment": "positive", "key_quote": "78% of respondents support a major marathon event if it includes community activities.", "topics": ["support", "community", "engagement", "survey"]},
    {"source": "East Las Vegas Neighborhood Watch Meeting (January 2026)", "sentiment": "negative", "key_quote": "Previous events ignored our neighborhood entirely. We want representation on the route.", "topics": ["inclusivity", "east las vegas", "diversity", "underserved"]},
    {"source": "Historic Westside Community Forum (December 2025)", "sentiment": "mixed", "key_quote": "Route through our neighborhood could highlight cultural heritage, but noise before 7am is unacceptable.", "topics": ["heritage", "noise", "westside", "culture", "early morning"]},
    {"source": "UNLV Student Government Resolution (January 2026)", "sentiment": "positive", "key_quote": "Student body voted unanimously to support marathon with 500+ student volunteers pledged.", "topics": ["volunteers", "students", "unlv", "youth", "engagement"]},
    {"source": "Spring Valley HOA Coalition Letter (February 2026)", "sentiment": "negative", "key_quote": "Road closures on Spring Mountain Road will trap 15,000 residents. Demand alternative access plan.", "topics": ["road closure", "access", "residential", "spring valley", "trapped"]},
]


def search(query: str) -> dict:
    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored = []
    for doc in SENTIMENT_DATABASE:
        score = 0
        for topic in doc["topics"]:
            if topic in query_lower:
                score += 3
            for word in query_words:
                if len(word) > 3 and word in topic:
                    score += 1
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:5]

    sentiments = [d["sentiment"] for _, d in top]
    return {
        "query": query,
        "total_results": len(top),
        "results": [{"source": d["source"], "sentiment": d["sentiment"], "key_quote": d["key_quote"]} for _, d in top],
        "sentiment_summary": {
            "positive": sentiments.count("positive"),
            "mixed": sentiments.count("mixed"),
            "negative": sentiments.count("negative"),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Search community sentiment")
    parser.add_argument("--query", required=True, help="Search query")
    args = parser.parse_args()
    result = search(args.query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
