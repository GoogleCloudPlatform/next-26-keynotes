"""Tools for the Marathon Planner Agent.

Contains:
- A2A infrastructure (SerializableRemoteA2aAgent, URL helpers)
- Remote A2A agent creators for Evaluator and Simulation Controller
- get_tools() — assembles all tools including SkillToolset
"""

import logging
import os

import httpx
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool
from a2a.client.client import ClientConfig as A2AClientConfig
from a2a.client.client_factory import ClientFactory as A2AClientFactory
from a2a.types import TransportProtocol as A2ATransport

from .auth import GoogleAuthRefresh
from ..evaluator.agent import root_agent as evaluator_agent

logger = logging.getLogger(__name__)

# Configurable timeout for Agent Engine requests (in seconds)
AGENT_TIMEOUT_SECONDS = 120


# ============================================================================
# A2A INFRASTRUCTURE
# ============================================================================


def _get_agent_a2a_endpoint(resource_name: str, default_port: int = 8080) -> str:
    """Construct A2A card endpoint URL from Agent Engine resource name or local address.

    Args:
        resource_name: Full resource name like:
            projects/123/locations/us-central1/reasoningEngines/456
            Or "local" / "local:PORT" for local agent discovery.
        default_port: Port to use if resource_name is "local" (without port)

    Returns:
        A2A endpoint URL for fetching the agent card
    """
    if resource_name.startswith("local"):
        if ":" in resource_name:
            port = resource_name.split(":")[1]
        else:
            port = default_port
        return f"http://127.0.0.1:{port}/.well-known/agent-card.json"

    parts = resource_name.split("/")
    try:
        location_idx = parts.index("locations") + 1
        location = parts[location_idx]
        api_endpoint = f"https://{location}-aiplatform.googleapis.com"
        return f"{api_endpoint}/v1beta1/{resource_name}/a2a/v1/card"
    except (ValueError, IndexError):
        # Fallback for non-standard resource names
        return resource_name


def _get_agent_a2a_url(resource_name: str) -> str | None:
    """Construct the regional A2A message URL from Agent Engine resource name.

    Agent Engine returns agent cards with a global URL
    (global-aiplatform.googleapis.com) that returns 404 for message:send.
    This constructs the correct regional URL.

    Args:
        resource_name: Full resource name like:
            projects/123/locations/us-central1/reasoningEngines/456

    Returns:
        Regional A2A URL for sending messages, or None for local agents
    """
    if resource_name.startswith("local"):
        return None

    parts = resource_name.split("/")
    location_idx = parts.index("locations") + 1
    location = parts[location_idx]

    api_endpoint = f"https://{location}-aiplatform.googleapis.com"
    return f"{api_endpoint}/v1beta1/{resource_name}/a2a"


class SerializableRemoteA2aAgent(RemoteA2aAgent):
    """RemoteA2aAgent with authentication and Agent Engine URL fix.

    Handles two Agent Engine issues:
    1. Creates httpx client lazily with Google Cloud auth and configurable timeout
    2. Fixes the agent card URL — Agent Engine returns a global URL that 404s
       on message:send; this overrides it with the correct regional URL
    """

    def __init__(self, *, a2a_url: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._a2a_url_override = a2a_url

    async def _ensure_httpx_client(self) -> httpx.AsyncClient:
        """Ensure httpx client exists with auth and proper factory config."""
        if self._httpx_client is None:
            self._httpx_client = httpx.AsyncClient(
                timeout=httpx.Timeout(timeout=AGENT_TIMEOUT_SECONDS),
                headers={"Content-Type": "application/json"},
                auth=GoogleAuthRefresh(),
            )
            self._httpx_client_needs_cleanup = True
            logger.debug(f"Created httpx client with {AGENT_TIMEOUT_SECONDS}s timeout")

        if self._a2a_client_factory is None:
            client_config = A2AClientConfig(
                httpx_client=self._httpx_client,
                streaming=False,
                polling=False,
                supported_transports=[A2ATransport.http_json, A2ATransport.jsonrpc],
            )
            self._a2a_client_factory = A2AClientFactory(config=client_config)
            logger.debug("Created A2A client factory with http_json transport")

        return self._httpx_client

    async def _resolve_agent_card_from_url(self, url: str):
        """Resolve agent card and fix URL for Agent Engine compatibility."""
        card = await super()._resolve_agent_card_from_url(url)
        if self._a2a_url_override:
            logger.info(
                f"Overriding agent card URL: {card.url} → {self._a2a_url_override}"
            )
            card.url = self._a2a_url_override
        return card





def create_evaluator_tool() -> AgentTool:
    """Create Evaluator Agent tool mapping to local agent."""
    return AgentTool(agent=evaluator_agent)




def create_simulator_agent() -> RemoteA2aAgent:
    """Create remote connection to Simulation Controller Agent via A2A.

    Returns:
        SerializableRemoteA2aAgent: Simulation Controller Agent proxy

    Raises:
        ValueError: If SIMULATOR_AGENT_RESOURCE_NAME not set
    """
    resource_name = os.environ.get("SIMULATOR_AGENT_RESOURCE_NAME")
    if not resource_name:
        raise ValueError("SIMULATOR_AGENT_RESOURCE_NAME environment variable must be set")

    endpoint = _get_agent_a2a_endpoint(resource_name, default_port=8089)
    logger.info(f"Creating Simulation Controller Agent connection: {endpoint}")

    return SerializableRemoteA2aAgent(
        name="simulator_agent",
        description=(
            "Simulation Controller Agent for marathon plans. "
            "Reviews plans for simulation readiness, assessing route feasibility, "
            "logistics completeness, and safety clearance. Returns structured "
            "SimulationApproval with approval decision, blockers, and recommendations."
        ),
        agent_card=endpoint,
        a2a_url=_get_agent_a2a_url(resource_name),
    )


def create_simulation_controller_tool() -> AgentTool:
    """Create Simulation Controller Agent tool."""
    return AgentTool(agent=create_simulator_agent())


# ============================================================================
# TOOL EXPORT
# ============================================================================

def get_tools() -> list:
    """Return the tools for the Marathon Planner Agent.

    Includes:
    - SkillToolset with 2 consolidated ADK Skills
    - PreloadMemoryTool for cross-session memory
    - Local AgentTool for Evaluator
    - A2A tool for Simulation Controller (if env var set)
    - Route planning tools (loaded dynamically from skill)

    Returns:
        List of ADK tools for this agent.
    """
    import pathlib
    import importlib.util
    from google.adk.skills import load_skill_from_dir
    from google.adk.tools.preload_memory_tool import PreloadMemoryTool
    from google.adk.tools.skill_toolset import SkillToolset

    # Load ADK Skills (2 consolidated skills)
    skills_dir = pathlib.Path(__file__).parent.parent / "skills"
    skills = [
        load_skill_from_dir(skills_dir / name)
        for name in sorted(skills_dir.iterdir())
        if name.is_dir() and not name.name.startswith("_")
    ]

    skill_toolset = SkillToolset(skills=skills)

    # Load tools from skills using importlib to handle hyphenated directory names
    def load_tool_from_skill(skill_name: str, tool_name: str):
        skill_tool_path = skills_dir / skill_name / "tools.py"
        if not skill_tool_path.exists():
            logger.warning(f"Tool file not found: {skill_tool_path}")
            return None
        try:
            spec = importlib.util.spec_from_file_location(f"{skill_name}.tools", skill_tool_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, tool_name, None)
        except Exception as e:
            logger.error(f"Error loading tool {tool_name} from {skill_name}: {e}")
            return None

    plan_marathon_route_func = load_tool_from_skill("route-planning", "plan_marathon_route")
    add_water_stations_func = load_tool_from_skill("route-planning", "add_water_stations")
    add_medical_tents_func = load_tool_from_skill("route-planning", "add_medical_tents")

    tools = [
        skill_toolset,
        PreloadMemoryTool(),
    ]

    if plan_marathon_route_func:
        tools.append(FunctionTool(func=plan_marathon_route_func))
    if add_water_stations_func:
        tools.append(FunctionTool(func=add_water_stations_func))
    if add_medical_tents_func:
        tools.append(FunctionTool(func=add_medical_tents_func))

    # Add local/A2A agent tools
    a2a_agents = [
        ("SIMULATOR_AGENT_RESOURCE_NAME", create_simulation_controller_tool),
    ]

    # Always add local evaluator
    tools.append(create_evaluator_tool())
    logger.info("Added local Evaluator tool")

    connected_agents = ["evaluator"]
    for env_var, creator in a2a_agents:
        if os.environ.get(env_var):
            tools.append(creator())
            logger.info(f"Added A2A tool: {env_var}")
            agent_name = env_var.replace("_AGENT_RESOURCE_NAME", "").lower()
            connected_agents.append(agent_name)
        else:
            logger.debug(f"Skipping A2A tool: {env_var} not set")

    if connected_agents:
        names = ", ".join(connected_agents)
        logger.info(f"Marathon Planner: A2A agents connected: {names}")
    else:
        logger.info("Marathon Planner: No A2A agents connected — standalone mode")

    return tools
