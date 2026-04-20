import os
import vertexai
from vertexai import Client
from dotenv import load_dotenv, set_key
import sys

def setup_agent_engine():
    # Load environment variables from .env
    env_path = ".env"
    load_dotenv(env_path)

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not found in .env. Please set it first.")
        sys.exit(1)

    vertexai.init(project=project_id, location=location)

    try:
        # Check if AGENT_ENGINE_ID is already set
        existing_id = os.environ.get("AGENT_ENGINE_ID")
        if existing_id:
            print(f"AGENT_ENGINE_ID already set: {existing_id}")
            return

        print("Creating Agent Engine instance...")
        
        client = Client(project=project_id, location=location)
        agent_engine = client.agent_engines.create()
        
        # The resource name has the format: projects/{project}/locations/{location}/reasoningEngines/{id}
        agent_engine_id = agent_engine.api_resource.name.split("/")[-1]

        print(f"Successfully created Agent Engine. ID: {agent_engine_id}")
        
        # Update .env file
        set_key(env_path, "AGENT_ENGINE_ID", agent_engine_id)
        print(f"Updated {env_path} with AGENT_ENGINE_ID={agent_engine_id}")

    except Exception as e:
        print(f"Error: Failed to create Agent Engine instance: {e}")
        print("Ensure you have the 'roles/aiplatform.user' role and the Vertex AI API is enabled.")
        sys.exit(1)

if __name__ == "__main__":
    setup_agent_engine()
