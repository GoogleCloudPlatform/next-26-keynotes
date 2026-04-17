"""Deploy the Simulation Controller Agent to Vertex AI Agent Engine.

Usage:
    uv run python -m src.simulator_agent.runtime.deploy
"""

import logging
import os

import vertexai
from a2a.types import TransportProtocol
from dotenv import load_dotenv
from vertexai.preview.reasoning_engines import A2aAgent

from ..core.config import MODEL
from ..services.memory_manager import create_simulation_controller_memory_topics

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()


def deploy_simulation_controller():
    """Deploy Simulation Controller Agent to Vertex AI Agent Engine wrapped in A2A."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = os.getenv("BUCKET_URI")

    if not all([project_id, staging_bucket]):
        raise ValueError("Set GOOGLE_CLOUD_PROJECT and BUCKET_URI in .env file")

    client = vertexai.Client(project=project_id, location=location)

    print("=" * 60)
    print("Deploying Simulation Controller Agent to Vertex AI Agent Engine")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print(f"Staging Bucket: {staging_bucket}")
    print(f"Model: {MODEL}")
    print("Memory Bank: Enabled with custom topics")
    print()

    from .agent_card import create_simulation_controller_card
    from .agent_executor import SimulationControllerExecutor

    agent_card = create_simulation_controller_card()
    agent_card.preferred_transport = TransportProtocol.http_json

    a2a_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=SimulationControllerExecutor,
    )

    memory_topics = create_simulation_controller_memory_topics()

    print("Step 1: Creating Agent Engine with Memory Bank...")

    deployed_agent = client.agent_engines.create(
        config={
            "staging_bucket": staging_bucket,
            "display_name": "Simulation Controller Agent",
            "description": (
                "Simulation Controller Agent - Reviews marathon plans for "
                "simulation readiness. Memory-enabled."
            ),
            "context_spec": {
                "memory_bank_config": {
                    "customization_configs": [memory_topics]
                }
            },
        }
    )

    agent_engine_id = deployed_agent.api_resource.name.split("/")[-1]
    print(f"Agent Engine created with ID: {agent_engine_id}")

    print("\nStep 2: Updating Agent Engine with agent and dependencies...")

    deployed_agent = client.agent_engines.update(
        name=deployed_agent.api_resource.name,
        agent=a2a_agent,
        config={
            "staging_bucket": staging_bucket,
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.121.0",
                "google-adk>=1.25.0",
                "a2a-sdk>=0.3.9",
                "pydantic>=2.12.0",
            ],
            "extra_packages": ["src/simulator_agent"],
            "env_vars": {
                "AGENT_ENGINE_ID": agent_engine_id,
                "AGENT_ENGINE_LOCATION": location,
                "SIMULATOR_MODEL": os.getenv("SIMULATOR_MODEL", MODEL),
            },
        },
    )

    resource_name = deployed_agent.api_resource.name
    api_endpoint = f"https://{location}-aiplatform.googleapis.com"
    a2a_endpoint = f"{api_endpoint}/v1beta1/{resource_name}/a2a/v1/card"

    print(f"\n{'=' * 60}")
    print("Simulation Controller Agent deployed successfully!")
    print(f"{'=' * 60}")
    print(f"Agent Resource Name: {resource_name}")
    print(f"Agent Engine ID: {agent_engine_id}")
    print(f"A2A Endpoint: {a2a_endpoint}")
    print()
    print("Add this to your .env file:")
    print(f'SIMULATOR_AGENT_RESOURCE_NAME="{resource_name}"')
    print("=" * 60)

    return deployed_agent


if __name__ == "__main__":
    deploy_simulation_controller()
