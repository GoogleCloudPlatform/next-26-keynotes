"""Local A2A server for testing the Simulation Controller Agent.

Usage:
    uv run python -m src.simulator_agent.runtime.local_server
"""

import asyncio
import logging
import os

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

AGENT_PORT = 8089


async def run_server():
    """Run the Simulation Controller Agent as a local A2A server."""
    from .agent_card import create_simulation_controller_card
    from .agent_executor import SimulationControllerExecutor

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError("GOOGLE_CLOUD_PROJECT must be set. Check .env file.")

    print("=" * 60)
    print("Starting Simulation Controller Agent Local A2A Server")
    print("=" * 60)

    agent_card = create_simulation_controller_card()
    executor = SimulationControllerExecutor()

    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    config = uvicorn.Config(
        app.build(),
        host="127.0.0.1",
        port=AGENT_PORT,
        log_level="info",
        loop="none",
    )

    print(f"Simulation Controller A2A server: http://127.0.0.1:{AGENT_PORT}")
    print(
        f"Agent card: http://127.0.0.1:{AGENT_PORT}/.well-known/agent.json"
    )
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())
