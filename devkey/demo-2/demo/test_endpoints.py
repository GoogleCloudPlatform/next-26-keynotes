"""End-to-end test for demo Cloud Run endpoints.

Verifies both solo and full-team services are healthy and can process
the demo prompt. Run after deploying with `cd demo/deploy && terraform apply`.

Usage:
    uv run python -m demo.test_endpoints              # test both
    uv run python -m demo.test_endpoints --solo        # test solo only
    uv run python -m demo.test_endpoints --full        # test full only
    uv run python -m demo.test_endpoints --health-only # agent card check only
"""

import argparse
import json
import sys
import time
import uuid

import httpx

from demo.scenarios import SCENARIOS

# Default timeout for agent orchestration (can take 2-3 min in full mode)
REQUEST_TIMEOUT = 300


def get_endpoint_urls() -> dict[str, str]:
    """Get endpoint URLs from Terraform output."""
    import subprocess

    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd="demo/deploy",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error reading terraform output: {result.stderr}")
        print("Have you deployed? Run: cd demo/deploy && terraform apply")
        sys.exit(1)

    outputs = json.loads(result.stdout)
    return {
        "solo": outputs["solo_url"]["value"],
        "full": outputs["full_url"]["value"],
    }


def check_agent_card(url: str, label: str) -> bool:
    """Verify the agent card endpoint returns valid JSON."""
    endpoint = f"{url}/.well-known/agent.json"
    print(f"  [{label}] GET {endpoint}")
    try:
        resp = httpx.get(endpoint, timeout=30, follow_redirects=True)
        if resp.status_code == 200:
            card = resp.json()
            name = card.get("name", "unknown")
            print(f"  [{label}] OK — agent: {name}")
            return True
        else:
            print(f"  [{label}] FAIL — status {resp.status_code}")
            return False
    except Exception as e:
        print(f"  [{label}] FAIL — {e}")
        return False


def send_demo_prompt(url: str, label: str, prompt: str) -> dict | None:
    """Send the demo prompt via A2A JSON-RPC and return the response."""
    msg_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": msg_id,
        "params": {
            "message": {
                "messageId": msg_id,
                "role": "user",
                "parts": [{"kind": "text", "text": prompt}],
            }
        },
    }

    print(f"  [{label}] POST {url}")
    print(f"  [{label}] Prompt: {prompt[:80]}...")
    start = time.time()

    try:
        resp = httpx.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        elapsed = time.time() - start
        print(f"  [{label}] Response in {elapsed:.1f}s (status {resp.status_code})")

        if resp.status_code == 200:
            data = resp.json()
            # Extract text from response parts
            result = data.get("result", {})
            parts = (
                result.get("artifacts", [{}])[0].get("parts", [])
                if result.get("artifacts")
                else []
            )
            text = ""
            for part in parts:
                if part.get("kind") == "text":
                    text += part.get("text", "")

            if text:
                # Show first 500 chars of response
                preview = text[:500] + ("..." if len(text) > 500 else "")
                print(f"  [{label}] Response preview:\n{preview}")
            else:
                print(f"  [{label}] Raw response: {json.dumps(data, indent=2)[:500]}")

            return data
        else:
            print(f"  [{label}] FAIL — {resp.text[:300]}")
            return None

    except httpx.TimeoutException:
        elapsed = time.time() - start
        print(f"  [{label}] TIMEOUT after {elapsed:.1f}s")
        return None
    except Exception as e:
        print(f"  [{label}] ERROR — {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Test demo endpoints")
    parser.add_argument("--solo", action="store_true", help="Test solo endpoint only")
    parser.add_argument("--full", action="store_true", help="Test full endpoint only")
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="Only check agent cards (no prompt)",
    )
    args = parser.parse_args()

    # Default: test both
    test_solo = args.solo or (not args.solo and not args.full)
    test_full = args.full or (not args.solo and not args.full)

    urls = get_endpoint_urls()
    prompt = SCENARIOS["solo"].demo_prompt  # same prompt for both

    passed = True

    # Health checks
    print("\n=== Agent Card Health Checks ===\n")
    if test_solo:
        if not check_agent_card(urls["solo"], "solo"):
            passed = False
    if test_full:
        if not check_agent_card(urls["full"], "full"):
            passed = False

    if args.health_only:
        print(f"\n{'PASSED' if passed else 'FAILED'}")
        sys.exit(0 if passed else 1)

    # Send demo prompts
    if test_solo:
        print("\n=== Solo Mode (Evaluator Only) ===\n")
        scenario = SCENARIOS["solo"]
        print(f"  Expected: {scenario.expected_behavior.splitlines()[0]}")
        print()
        result = send_demo_prompt(urls["solo"], "solo", prompt)
        if result is None:
            passed = False

    if test_full:
        print("\n=== Full Team Mode (All Sub-Agents) ===\n")
        scenario = SCENARIOS["full_team"]
        print(f"  Expected: {scenario.expected_behavior.splitlines()[0]}")
        print()
        result = send_demo_prompt(urls["full"], "full", prompt)
        if result is None:
            passed = False

    print(f"\n{'PASSED' if passed else 'FAILED'}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
