"""Deploy the {{AGENT_DISPLAY_NAME}} to Vertex AI Agent Engine.

Usage:
    uv run python -m src.{{AGENT_MODULE}}.runtime.deploy

Two-step deployment: create empty Agent Engine, then update with agent.
"""

import logging
import os

import vertexai
from a2a.types import TransportProtocol
from dotenv import load_dotenv
from vertexai.preview.reasoning_engines import A2aAgent

from ..core.config import MODEL
from ..services.memory_manager import {{MEMORY_FUNC}}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
load_dotenv()


def {{DEPLOY_FUNC}}():
    """Deploy {{AGENT_DISPLAY_NAME}} to Vertex AI Agent Engine wrapped in A2A."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = os.getenv("BUCKET_URI")

    if not all([project_id, staging_bucket]):
        raise ValueError("Set GOOGLE_CLOUD_PROJECT and BUCKET_URI in .env file")

    client = vertexai.Client(project=project_id, location=location)

    print("=" * 60)
    print("Deploying {{AGENT_DISPLAY_NAME}} to Vertex AI Agent Engine")
    print("=" * 60)
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print(f"Staging Bucket: {staging_bucket}")
    print(f"Model: {MODEL}")
    print("Memory Bank: Enabled with custom topics")
    print()

    from .agent_card import {{CARD_FUNC}}
    from .agent_executor import {{EXECUTOR_CLASS}}

    agent_card = {{CARD_FUNC}}()
    agent_card.preferred_transport = TransportProtocol.http_json

    a2a_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder={{EXECUTOR_CLASS}},
    )

    memory_topics = {{MEMORY_FUNC}}()

    print("Step 1: Creating Agent Engine with Memory Bank...")

    deployed_agent = client.agent_engines.create(
        config={
            "staging_bucket": staging_bucket,
            "display_name": "{{AGENT_DISPLAY_NAME}}",
            "description": (
                # TODO: Add agent description for deployment
                "{{AGENT_DISPLAY_NAME}} - Memory-enabled agent with ADK Skills."
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
            "extra_packages": ["src/{{AGENT_MODULE}}"],
            "env_vars": {
                "AGENT_ENGINE_ID": agent_engine_id,
                "AGENT_ENGINE_LOCATION": location,
            },
        },
    )

    resource_name = deployed_agent.api_resource.name
    api_endpoint = f"https://{location}-aiplatform.googleapis.com"
    a2a_endpoint = f"{api_endpoint}/v1beta1/{resource_name}/a2a/v1/card"

    print(f"\n{'=' * 60}")
    print("{{AGENT_DISPLAY_NAME}} deployed successfully!")
    print(f"{'=' * 60}")
    print(f"Agent Resource Name: {resource_name}")
    print(f"Agent Engine ID: {agent_engine_id}")
    print(f"A2A Endpoint: {a2a_endpoint}")
    print()
    print("Add this to your .env file:")
    print(f'{{AGENT_PREFIX}}_AGENT_RESOURCE_NAME="{resource_name}"')
    print("=" * 60)

    return deployed_agent


if __name__ == "__main__":
    {{DEPLOY_FUNC}}()
