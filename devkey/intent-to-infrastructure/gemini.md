# Default Scope
Unless otherwise specified, assume the scope of my Google Cloud queries to be the following:
- project: projects/<project>
- region: asia-southeast1
- gke-cluster: https://container.googleapis.com/v1/projects/<project>/locations/asia-southeast1/clusters/hc-demo-cluster
- gke-namespace: default
- Model GCS bucket path: hc-demo-models-<project>

# GCP and Kubernetes Applications
GCP and Kubernetes resources and mutations should use MCP tools. These tools are specialized backend agents. As the client agent, your role is to identify the intent and delegate the entire task verbatim to the appropriate intelligent tool. 
1. Use the `ask_cloud_assist` tool for requests about GCP application context, except when the question is about Kubernetes.
2. Use the `design_infra` tool with the `generate_kubernetes_yaml` command for requests about Kubernetes. Existing yaml files must be passed in the `userQuery` as a markdown codeblock. 
3. Use `invoke_operation` to apply changes.

## Instructions and constraints
When answering any queries about Google Cloud Platform (GCP), YOU MUST follow these rules:

- **Context ID:** All Gemini Cloud Assist (GCA) tools accept a parameter of: "contextId" (string, optional): The context id of a multi-turn conversation. All GCA tools will return a contextId in their response. Any subsequent turns to a GCA tool must pass in the contextId as a parameter.
- **Direct Tool Mapping:** Upon receiving a request about GCP resources, immediately invoke the relevant tool.
- **No local files outside current directory:** Do not attempt to access or write to any files outside the current working directory.
- **Context Transfer:** Pass the user's entire prompt verbatim as the input query to the tool. 
- DO NOT Summarize , rephrase, or truncate the input. 
- DO NOT attempt to break the problem down and make intermediate queries to cloud assist
- DO include all identifiers (Project IDs, Cluster names, or Instance paths) found in the prompt. 
- DO send the user's query to the tools with any additional local context from the local directory.
- **Persistence to Local Workspace:** Any configuration, manifest, or YAML generated or updated by the tools must be persisted to the local workspace.
- **No local tools:** Do not run any local tools (e.g., `gcloud`, `kubectl`, etc.). Only use the MCP tool `ask_cloud_assist`.
- **No Local Validation:** Do not attempt to validate the existence of mentioned cloud resources or projects against local configuration files (e.g., `.gcloud/config` or `kubeconfig`). Always use an MCP tool to discover resources.
- **Execution follow up:** Always ask the user if they want to apply the yaml using `invoke_operation` after generating yaml. Explicitly ask: "Would you like to proceed with applying this configuration?". If the user confirms, invoke the `invoke_operation` tool to apply the manifests