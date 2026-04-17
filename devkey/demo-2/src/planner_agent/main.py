"""Cloud Run entrypoint for the Marathon Planner Agent.

This module provides the ASGI application for Cloud Run deployment.

Usage:
    # Locally with uvicorn
    uvicorn src.planner_agent.main:app --host 0.0.0.0 --port 8080

    # Cloud Run uses Gunicorn with Uvicorn workers
    gunicorn src.planner_agent.main:app -k uvicorn.workers.UvicornWorker

Simple is better than complex.
"""

import asyncio
import logging
import os

# IMPORTANT: Set environment variables BEFORE importing any google.genai modules
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global app instance - created on first request
_app_instance: Starlette | None = None
_app_lock = asyncio.Lock()


async def get_or_create_app() -> Starlette:
    """Get or create the A2A application instance."""
    global _app_instance

    if _app_instance is not None:
        return _app_instance

    async with _app_lock:
        if _app_instance is not None:
            return _app_instance

        from .runtime.agent_card import create_marathon_planner_card
        from .runtime.agent_executor import MarathonPlannerExecutor

        # Get base URL from environment (Cloud Run provides this)
        base_url = os.environ.get("APP_URL", "http://localhost:8080")

        logger.info("Initializing Marathon Planner Agent")
        logger.info(f"  Base URL: {base_url}")

        # Create agent card
        agent_card = create_marathon_planner_card()
        agent_card.url = base_url

        # Create executor
        executor = MarathonPlannerExecutor()

        from google.adk.runners import RunConfig
        from google.adk.agents.run_config import StreamingMode, ToolThreadPoolConfig
        from google.genai.types import ContextWindowCompressionConfig
        
        # Create A2A request handler
        request_handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore(),
        )

        # Create A2A application
        a2a_app = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        _app_instance = a2a_app.build()
        logger.info("Marathon Planner Agent initialized successfully")

        return _app_instance


# Create a wrapper app that lazily initializes the real app
async def lazy_app(scope, receive, send):
    """Lazy ASGI app wrapper that initializes on first request."""
    real_app = await get_or_create_app()
    await real_app(scope, receive, send)


# Export the app for uvicorn/gunicorn
app = lazy_app
