"""Delete deployed agents from Vertex AI Agent Engine.

Use this script to clean up deployed agents.

Usage:
    # Delete all agents
    uv run python -m src.utils.delete_agents

    # Delete specific agent by ID
    uv run python -m src.utils.delete_agents --id 7734823508357677056

    # List agents without deleting
    uv run python -m src.utils.delete_agents --list
"""

import os
import argparse
from dotenv import load_dotenv
import vertexai
from vertexai import agent_engines

# Load environment variables
load_dotenv()


def list_agents(project: str, location: str) -> list:
    """List all deployed agents.

    Args:
        project: GCP project ID
        location: GCP location

    Returns:
        List of agent resources
    """
    vertexai.init(project=project, location=location)

    agents = list(agent_engines.list())

    print(f"\nFound {len(agents)} deployed agent(s):")
    print("=" * 80)

    for agent in agents:
        print(f"  Name: {agent.display_name}")
        print(f"  Resource: {agent.resource_name}")
        print(f"  Created: {agent.create_time}")
        print(f"  ID: {agent.resource_name.split('/')[-1]}")
        print("-" * 80)

    return agents


def delete_agent(resource_name: str):
    """Delete a specific agent.

    Args:
        resource_name: Full resource name or agent ID
    """
    try:
        agent = agent_engines.get(resource_name)
        print(f"Deleting agent: {agent.display_name} ({resource_name})")
        agent.delete(force=True)
        print(f"  Deleted successfully!")
    except Exception as e:
        print(f"  Error deleting {resource_name}: {e}")


def delete_all_agents(project: str, location: str, confirm: bool = True):
    """Delete all deployed agents.

    Args:
        project: GCP project ID
        location: GCP location
        confirm: Whether to ask for confirmation
    """
    agents = list_agents(project, location)

    if not agents:
        print("No agents to delete.")
        return

    if confirm:
        response = input(f"\nDelete all {len(agents)} agent(s)? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            return

    print("\nDeleting agents...")
    for agent in agents:
        delete_agent(agent.resource_name)

    print("\nDone!")


def main():
    parser = argparse.ArgumentParser(
        description="Manage deployed agents on Vertex AI Agent Engine"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List agents without deleting"
    )
    parser.add_argument(
        "--id", type=str, help="Delete specific agent by ID or resource name"
    )
    parser.add_argument(
        "--all", action="store_true", help="Delete all agents (with confirmation)"
    )
    parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--project",
        type=str,
        default=os.getenv("GOOGLE_CLOUD_PROJECT"),
        help="GCP project ID",
    )
    parser.add_argument(
        "--location",
        type=str,
        default=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        help="GCP location",
    )

    args = parser.parse_args()

    if not args.project:
        print("Error: GOOGLE_CLOUD_PROJECT not set. Use --project or set in .env")
        return

    vertexai.init(project=args.project, location=args.location)

    if args.list:
        list_agents(args.project, args.location)
    elif args.id:
        # Handle both full resource name and just ID
        if "/" not in args.id:
            resource_name = f"projects/{args.project}/locations/{args.location}/reasoningEngines/{args.id}"
        else:
            resource_name = args.id
        delete_agent(resource_name)
    elif args.all:
        delete_all_agents(args.project, args.location, confirm=not args.force)
    else:
        # Default: list agents and ask what to do
        agents = list_agents(args.project, args.location)
        if agents:
            print("\nOptions:")
            print("  --list    : List agents only")
            print("  --id ID   : Delete specific agent")
            print("  --all     : Delete all agents")
            print("  --force   : Skip confirmation")


if __name__ == "__main__":
    main()
