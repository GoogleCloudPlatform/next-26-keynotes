import os
from dotenv import load_dotenv
from google.adk.tools import AgentRegistry, RemoteA2aAgent

# Load environment variables from .env
load_dotenv()

# initialize the client using context-aware environment variables
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
region = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

client = AgentRegistry(project_id=project_id, region=region)

# Fetch Agent Endpoint for a specific Agent from App Hub
agent = client.agents.get(name="simulator_agent") 

# Pass the endpoint details to the RemoteA2AAgent
remote_agent = RemoteA2aAgent(
    name="simulator_agent",
    description=(
        "Simulation Controller Agent - Reviews marathon plans for simulation "
        "readiness. Assesses route feasibility, logistics completeness, and "
        "safety clearance. Returns structured SimulationApproval."
    ),
    agent_card=agent.agentCardEndpoint.endpoint,
)
