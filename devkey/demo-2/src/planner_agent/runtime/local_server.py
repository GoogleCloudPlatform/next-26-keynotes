"""Local A2A server for testing the Marathon Planner Agent.

Run this to start a local A2A server, then use test_client.py to test.

Usage:
    uv run python -m src.planner_agent.runtime.local_server
"""

import os

from dotenv import load_dotenv

# Load environment variables BEFORE importing local modules
load_dotenv()

# IMPORTANT: Set environment variables BEFORE importing any google.genai modules
# The google.genai SDK reads these at import time
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

import asyncio

import uvicorn
import vertexai
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import TransportProtocol
from google.adk import Runner
from google.adk.a2a.executor.a2a_agent_executor import (
    A2aAgentExecutor,
    A2aAgentExecutorConfig,
)
from google.adk.sessions import InMemorySessionService

# Default port for this agent
AGENT_PORT = 8084


def create_marathon_planner_server():
    """Create an A2A server for the Marathon Planner Agent.

    Returns:
        A2AStarletteApplication instance ready to serve via uvicorn
    """
    from ..core import root_agent
    from .agent_card import create_marathon_planner_card

    runner = Runner(
        app_name=root_agent.name,
        agent=root_agent,
        session_service=InMemorySessionService(),
    )

    config = A2aAgentExecutorConfig()
    executor = A2aAgentExecutor(runner=runner, config=config)

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    agent_card = create_marathon_planner_card()
    agent_card.url = f"http://localhost:{AGENT_PORT}"
    agent_card.preferred_transport = TransportProtocol.jsonrpc

    return A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )


async def run_server():
    """Run the Marathon Planner Agent as a local A2A server."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT environment variable must be set. "
            "Check your .env file."
        )

    print("=" * 60)
    print("Starting Marathon Planner Agent Local A2A Server")
    print("=" * 60)
    print(f"Project: {project}")
    print(f"Location: {location}")
    print()

    app = create_marathon_planner_server()

    config = uvicorn.Config(
        app.build(),
        host="127.0.0.1",
        port=AGENT_PORT,
        log_level="info",
        loop="none",
    )

    print(f"Marathon Planner A2A server: http://127.0.0.1:{AGENT_PORT}")
    print(f"Agent card: http://127.0.0.1:{AGENT_PORT}/.well-known/agent-card.json")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())
