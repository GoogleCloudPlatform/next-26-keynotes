"""A2A Agent Executor for the {{AGENT_DISPLAY_NAME}}.

Handles A2A protocol execution with Vertex AI session and memory services.
"""

import json
import os

import vertexai
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, UnsupportedOperationError
from a2a.utils import new_agent_text_message
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.genai import types

from ..services.memory_manager import create_memory_service
from ..services.session_manager import SessionManager, create_session_service

logger = __import__("logging").getLogger(__name__)


class {{EXECUTOR_CLASS}}(AgentExecutor):
    """A2A Agent Executor for the {{AGENT_DISPLAY_NAME}}."""

    def __init__(self):
        self.agent = None
        self.runner = None
        self.session_manager: SessionManager | None = None

    def _init_agent(self) -> None:
        """Lazy initialization of the agent and ADK Runner."""
        if self.agent is None:
            # Absolute import for deployed agent (bundled as top-level package)
            # Falls back to relative import for local development
            try:
                from {{AGENT_MODULE}}.agent import root_agent
            except ImportError:
                from ..core import root_agent

            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

            if not project_id:
                raise ValueError(
                    "GOOGLE_CLOUD_PROJECT environment variable required"
                )

            vertexai.init(project=project_id, location=location)
            self.agent = root_agent

        if self.runner is None:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            session_location = (
                os.environ.get("AGENT_ENGINE_LOCATION")
                or os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            )

            session_service = create_session_service(
                project=project_id,
                location=session_location,
            )

            memory_service = create_memory_service(
                project=project_id,
                location=session_location,
            )

            self.runner = Runner(
                app_name=self.agent.name,
                agent=self.agent,
                session_service=session_service,
                memory_service=memory_service,
            )

        if self.session_manager is None:
            self.session_manager = SessionManager(
                session_service=self.runner.session_service,
                cache_maxsize=1000,
                cache_ttl=3600,
            )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a request from the A2A protocol."""
        if self.agent is None:
            self._init_agent()

        user_id = (
            context.message.metadata.get("user_id")
            if context.message and context.message.metadata
            else "planner_agent"
        )

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not hasattr(context, "current_task") or not context.current_task:
            await updater.submit()

        await updater.start_work()

        query = context.get_user_input()

        if not query:
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message("No request provided"),
                final=True,
            )
            return

        logger.info(f"{{AGENT_DISPLAY_NAME}} received: {query[:100]}...")

        try:
            await updater.update_status(
                TaskState.working,
                message=new_agent_text_message("Processing request..."),
            )

            session_id = await self.session_manager.get_or_create_session(
                context_id=context.context_id,
                app_name=self.runner.app_name,
                user_id=user_id,
            )

            content = types.Content(
                role="user",
                parts=[types.Part(text=query)],
            )

            final_event = None
            async for event in self.runner.run_async(
                session_id=session_id,
                user_id=user_id,
                new_message=content,
            ):
                if event.is_final_response():
                    final_event = event

            if final_event and final_event.content and final_event.content.parts:
                response_text = "".join(
                    part.text
                    for part in final_event.content.parts
                    if hasattr(part, "text") and part.text
                )

                if response_text:
                    try:
                        parsed = json.loads(response_text)
                        if "{{VALIDATION_FIELD}}" not in parsed:
                            raise ValueError("Missing '{{VALIDATION_FIELD}}' field")
                    except (json.JSONDecodeError, ValueError):
                        pass

                    await updater.add_artifact(
                        [TextPart(text=response_text)],
                        name="{{ARTIFACT_NAME}}",
                    )
                    await updater.complete()
                    return

            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message("Failed to generate response"),
                final=True,
            )

        except Exception as e:
            logger.error(f"{{AGENT_DISPLAY_NAME}} error: {e}", exc_info=True)
            await updater.update_status(
                TaskState.failed,
                message=new_agent_text_message(
                    f"Request failed: {str(e)[:200]}"
                ),
                final=True,
            )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise ServerError(error=UnsupportedOperationError())
