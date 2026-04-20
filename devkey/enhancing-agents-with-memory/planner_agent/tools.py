import asyncio
import os
import threading

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import google.auth
import google.auth.transport.requests

region = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
cluster_id = os.environ.get("ALLOYDB_CLUSTER_ID", "rules-db")
instance_id = f"{cluster_id}-primary"

# Managed AlloyDB MCP endpoint for the specific region
url = f"https://alloydb.{region}.rep.googleapis.com/mcp"
full_instance_name = f"projects/{project_id}/locations/{region}/clusters/{cluster_id}/instances/{instance_id}"

def get_auth_headers():
    # Configure authentication for the MCP server
    credentials, project = google.auth.default(scopes="https://www.googleapis.com/auth/cloud-platform")
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }
    return headers

async def get_local_and_traffic_rules(query: str) -> str:
    """
    Uses vector search in AlloyDB to find relevant local and traffic rules.
    This tool connects to the managed remote AlloyDB MCP server provided by Google Cloud.
    """
    # Vector search query for rules.
    sql = f"""
    SELECT text FROM rules WHERE city = 'Las Vegas'
    ORDER BY embedding <=> google_ml.embedding('gemini-embedding-001', '{query}')::vector 
    ASC LIMIT 5;
    """
    # Establish a streamable HTTP connection to the MCP server
    async with streamablehttp_client(url, headers=get_auth_headers()) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            # Call the 'execute_sql' tool provided by the AlloyDB MCP server
            result = await session.call_tool(
                "execute_sql",
                arguments={
                    "instance": full_instance_name,
                    "database": "compliance_rules",
                    "sqlStatement": sql
                }
            )
            output = []
            for content in result.content:
                if hasattr(content, 'text'):
                    output.append(content.text)
            return "\n".join(output)
