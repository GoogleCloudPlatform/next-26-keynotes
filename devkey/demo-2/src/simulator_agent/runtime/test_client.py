"""Test client for the Simulation Controller Agent A2A server.

Usage:
    # Terminal 1: Start server
    uv run python -m src.simulator_agent.runtime.local_server

    # Terminal 2: Run test client
    uv run python -m src.simulator_agent.runtime.test_client
"""

import asyncio
import json
import uuid

import httpx


AGENT_URL = "http://localhost:8089"


async def test_agent():
    """Test the Simulation Controller Agent via A2A protocol."""
    print("=" * 60)
    print("Testing Simulation Controller Agent via A2A")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=120.0) as http_client:
        # Fetch the agent card
        print("1. Fetching agent card...")
        card_response = await http_client.get(
            f"{AGENT_URL}/.well-known/agent.json"
        )

        if card_response.status_code != 200:
            print(f"   Error: Could not fetch agent card (status {card_response.status_code})")
            print("   Make sure local_server.py is running!")
            return

        agent_card = card_response.json()
        print(f"   Agent: {agent_card.get('name')}")
        print(f"   Description: {agent_card.get('description', '')[:60]}...")
        print()

        print("2. Test: Review a sample marathon plan")
        print("-" * 40)
        sample_plan = (
            "Marathon plan for Las Vegas, March 2026, 15,000 participants. "
            "Route: 26.2 miles starting at Mandalay Bay, through the Strip, "
            "Fremont Street, Arts District, and back. "
            "22 water stations, 5 medical tents, chip timing system. "
            "Emergency vehicle access maintained with crossing points every 2 miles. "
            "Budget: $2M costs, $3M projected revenue from registration and sponsors. "
            "Race day schedule: 4am setup, 6am start, 12pm course closes."
        )
        await send_request(http_client, sample_plan)
        print()

    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


async def send_request(client: httpx.AsyncClient, request_data: str):
    """Send a request via A2A JSON-RPC."""
    message_id = str(uuid.uuid4())

    payload = {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [{"kind": "text", "text": request_data}],
            },
            "configuration": {
                "acceptedOutputModes": ["text"],
            },
        },
    }

    print("   Sending request...")

    try:
        response = await client.post(
            f"{AGENT_URL}/",
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            print(f"   Error: HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
            return

        result = response.json()

        if "error" in result:
            print(f"   Error: {result['error']}")
            return

        if "result" in result:
            task_result = result["result"]

            if "artifacts" in task_result:
                for artifact in task_result["artifacts"]:
                    for part in artifact.get("parts", []):
                        if part.get("kind") == "text":
                            response_text = part.get("text", "")
                            print("   Response:")
                            try:
                                parsed = json.loads(response_text)
                                print(f"   {json.dumps(parsed, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"   {response_text}")
            else:
                status = task_result.get("status", {})
                state = status.get("state", "unknown")
                print(f"   Task state: {state}")

    except httpx.ConnectError:
        print("   Error: Could not connect to server")
        print("   Make sure local_server.py is running!")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_agent())
