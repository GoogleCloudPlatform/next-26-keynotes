import sys
import json
from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.agents import LoopAgent
from functools import cached_property
import logging
from opentelemetry import trace
from typing import AsyncGenerator
from google.adk.models import Gemini, LlmResponse
from google.genai import Client, types
from google.adk.agents import LlmAgent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset
from .config import AGENT_NAME, OUTPUT_SCHEMA
from .prompts import INSTRUCTION, COMPACTION_PROMPT_TEMPLATE
from .tools import get_tools
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.events.event import Event
import time

# read .env
import os
from dotenv import load_dotenv

MODEL = "gemini-2.5-flash"

load_dotenv()
# verify env vars are loaded
print("🌈 ENV VARS")
print(f"GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID')}")
print(f"GCP_LOCATION: {os.getenv('GCP_LOCATION')}")


class CloudLoggingJsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "message": record.getMessage(),
            "severity": record.levelname,
        }

        # In standard logging, keys in 'extra' are bound directly to the LogRecord.
        if hasattr(record, "logging.googleapis.com/trace"):
            log_entry["logging.googleapis.com/trace"] = getattr(
                record, "logging.googleapis.com/trace"
            )
        if hasattr(record, "logging.googleapis.com/spanId"):
            log_entry["logging.googleapis.com/spanId"] = getattr(
                record, "logging.googleapis.com/spanId"
            )

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Clean up existing handlers to prevent duplicate text output if a handler is inherited
logger.handlers = []
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
handler.setFormatter(CloudLoggingJsonFormatter())
logger.addHandler(handler)
logger.propagate = False  # Prevent standard text formatters from wrapping it!


class Gemini3(Gemini):
    @cached_property
    def api_client(self) -> Client:
        project = os.getenv("GCP_PROJECT_ID")
        location = (
            "global"  # must hardcode to global, gemini 3 flash is only available here
        )

        return Client(
            vertexai=True,
            project=project,
            location=location,
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
            ),
        )

    async def generate_content_async(
        self, llm_request, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        """Wrap the LLM call to log exceptions using standard Python logging."""
        try:
            async for response in super().generate_content_async(llm_request, stream):
                yield response
        except Exception as e:
            # Capture the exception in standard Python logging (Cloud Logging)
            span = trace.get_current_span()
            extra = {}
            if span and span.get_span_context().is_valid:
                ctx = span.get_span_context()
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
                extra["logging.googleapis.com/trace"] = (
                    f"projects/{os.getenv('GCP_PROJECT_ID')}/traces/{trace_id}"
                )
                extra["logging.googleapis.com/spanId"] = span_id

            logger.exception(
                "Exception in LLM call captured by Gemini3 wrapper", extra=extra
            )
            raise e


# Note - downgraded to Gemini 2.5 to avoid unexpected capacity issues with Gemini 3
llm = Gemini3(model=MODEL)


# Define a custom summarizer that can "see" into the JSON tool response (vs. just raw text by default)
class ToolAwareSummarizer(LlmEventSummarizer):
    def _format_events_for_prompt(self, events: list[Event]) -> str:
        print(
            f"\n[🗜️ COMPACTION TRIGGERED] Formatting {len(events)} events for summarization..."
        )
        print(
            "[💤 DEMO DELAY] Sleeping for 30 seconds to reset Vertex TPM quota before the summarizer LLM call..."
        )
        time.sleep(30)
        formatted_history = []
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        formatted_history.append(f"{event.author}: {part.text}")
                    elif part.function_call:
                        # Capture what tool the agent decided to use
                        formatted_history.append(
                            f"{event.author} (Tool Call): {part.function_call.name} with args: {part.function_call.args}"
                        )
                    elif part.function_response:
                        # Capture the massive JSON payload returned to the agent
                        formatted_history.append(
                            f"{event.author} (Tool Response): {part.function_response.name} returned {part.function_response.response}"
                        )
        return "\n".join(formatted_history)


summarizer = ToolAwareSummarizer(llm=llm, prompt_template=COMPACTION_PROMPT_TEMPLATE)

_skill_toolset = SkillToolset(skills=[])

_tools = [
    *get_tools(),
]

_agent_kwargs = dict(
    name=AGENT_NAME,
    model=Gemini3(model=MODEL),
    description="Simulator Agent responsible for executing the Rolling Field Audit on marathon runner telemetry.",
    instruction=INSTRUCTION,
    tools=_tools,
)

if OUTPUT_SCHEMA is not None:
    _agent_kwargs["output_schema"] = OUTPUT_SCHEMA

_underlying_agent = LlmAgent(**_agent_kwargs)
root_agent = LoopAgent(
    name="simulator_loop", sub_agents=[_underlying_agent], max_iterations=1
)

app = App(
    name="simulator_agent",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,
        overlap_size=1,
        summarizer=summarizer,
        token_threshold=200000,
        event_retention_size=2,
    ),
)
