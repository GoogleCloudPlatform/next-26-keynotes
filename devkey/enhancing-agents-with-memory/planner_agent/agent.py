import os
import vertexai
import pathlib
from google.adk.agents import LlmAgent
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset
from vertexai.agent_engines import AdkApp
from .tools import get_local_and_traffic_rules

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
# Use GOOGLE_CLOUD_REGION for regional services like Memory Bank and Sessions
REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
AGENT_ENGINE_ID = os.environ.get("AGENT_ENGINE_ID")

# Initialize Vertex AI for regional services
if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=REGION)

# 1. Configure Agent Platform Sessions for conversation persistence
def session_service_builder():
    """Builder for Agent Platform Sessions."""
    return VertexAiSessionService(project=PROJECT_ID, location=REGION)

# 2. Configure Agent Platform Memory Bank for long-term learning
def memory_service_builder():
    """Builder for Agent Platform Memory Bank."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=REGION,
        agent_engine_id=AGENT_ENGINE_ID
    )

async def auto_save_memories(callback_context):
    """Callback to ingest the session into the memory bank after each turn."""
    # Note: In AdkApp, the memory service is available via the invocation context
    if hasattr(callback_context._invocation_context, 'memory_service') and callback_context._invocation_context.memory_service:
        await callback_context._invocation_context.memory_service.add_session_to_memory(
            callback_context._invocation_context.session
        )

# 3. Load Agent Skills
alloydb_skill = load_skill_from_dir(pathlib.Path(__file__).parent / "skills" / "get-local-and-traffic-rules")

# 4. Assemble the root agent with tools, skills, and memory callbacks
# Note: Preview models like gemini-3-flash-preview are currently only available on the global endpoint.
root_agent = LlmAgent(
    name="planner_agent",
    model="gemini-3-flash-preview",
    instruction="""
    You are a helpful marathon planning assistant. 
    You help users plan their races and ensure they follow local city rules.
    Always use the 'get_local_and_traffic_rules' tool if a specific location (like Las Vegas) is mentioned 
    to ensure the plan is following local rules.
    """,
    tools=[
        get_local_and_traffic_rules,
        skill_toolset.SkillToolset(skills=[alloydb_skill])
    ],
    after_agent_callback=[auto_save_memories],
)

# 5. Wrap the agent in an AdkApp to manage the stateful lifecycle
app = AdkApp(
    agent=root_agent,
    session_service_builder=session_service_builder,
    memory_service_builder=memory_service_builder
)
