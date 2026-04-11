# Terraform configuration for Marathon Planner Agent on Cloud Run
#
# Deploys the Marathon Planner Agent as a Cloud Run service that calls
# Evaluator and Simulation Controller agents via A2A protocol.
# Powered by Gemini 3 Flash Preview.

# ============================================================================
# VARIABLES
# ============================================================================

variable "orchestrator_image" {
  description = "Container image for Marathon Planner Agent (leave empty to build from source)"
  type        = string
  default     = ""
}

# Agent Engine resource names for A2A agents
variable "evaluator_agent_resource_name" {
  description = "Resource name of deployed Evaluator Agent"
  type        = string
  # Set in terraform.tfvars after deploying the agent
}

variable "simulator_agent_resource_name" {
  description = "Resource name of deployed Simulation Controller Agent"
  type        = string
  # Set in terraform.tfvars after deploying the agent
}

variable "planner_model" {
  description = "Gemini model for the Marathon Planner Agent"
  type        = string
  default     = "gemini-2.5-flash"
}

# ============================================================================
# SERVICE ACCOUNT
# ============================================================================

resource "google_service_account" "orchestrator" {
  account_id   = "orchestrator-agent"
  display_name = "Orchestrator Agent Service Account"
  description  = "Service account for Marathon Planner Agent Cloud Run service"
}

# Grant Vertex AI User role to call Gemini via Model Garden
resource "google_project_iam_member" "orchestrator_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

# Grant Cloud Run Invoker role to call Agent Engine agents
resource "google_project_iam_member" "orchestrator_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

# Grant Session User role for Agent Engine message interactions
resource "google_project_iam_member" "orchestrator_session_user" {
  project = var.project_id
  role    = "roles/aiplatform.sessionUser"
  member  = "serviceAccount:${google_service_account.orchestrator.email}"
}

# ============================================================================
# CLOUD RUN SERVICE
# ============================================================================

# Artifact Registry repository for container images
resource "google_artifact_registry_repository" "orchestrator" {
  location      = var.region
  repository_id = "orchestrator-agent"
  description   = "Container images for Marathon Planner Agent"
  format        = "DOCKER"

  labels = {
    purpose = "orchestrator-agent"
    demo    = "next26"
  }
}

# Cloud Run service for Marathon Planner Agent
resource "google_cloud_run_v2_service" "orchestrator" {
  name     = "orchestrator-agent"
  location = var.region

  deletion_protection = false

  template {
    service_account = google_service_account.orchestrator.email

    scaling {
      min_instance_count = 1  # Keep warm for demo
      max_instance_count = 10
    }

    containers {
      # Use provided image or default to Artifact Registry
      image = var.orchestrator_image != "" ? var.orchestrator_image : "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.orchestrator.repository_id}/orchestrator-agent:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8080
      }

      # Environment variables
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      # Gemini works in us-central1 (same as Agent Engine)
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "true"
      }

      # Model configuration
      env {
        name  = "PLANNER_MODEL"
        value = var.planner_model
      }

      # A2A agent resource names
      env {
        name  = "EVALUATOR_AGENT_RESOURCE_NAME"
        value = var.evaluator_agent_resource_name
      }

      env {
        name  = "SIMULATOR_AGENT_RESOURCE_NAME"
        value = var.simulator_agent_resource_name
      }

      # Startup and liveness probes
      startup_probe {
        http_get {
          path = "/.well-known/agent.json"
          port = 8080
        }
        initial_delay_seconds = 30
        period_seconds        = 10
        timeout_seconds       = 10
        failure_threshold     = 6
      }

      liveness_probe {
        http_get {
          path = "/.well-known/agent.json"
          port = 8080
        }
        period_seconds    = 30
        timeout_seconds   = 5
        failure_threshold = 3
      }
    }

    # Request timeout (10 minutes for complex orchestration)
    timeout = "600s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    purpose = "orchestrator-agent"
    demo    = "next26"
  }

  depends_on = [
    google_artifact_registry_repository.orchestrator,
  ]
}

# Allow unauthenticated access for demo (can be restricted for production)
variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run service"
  type        = bool
  default     = false
}

resource "google_cloud_run_v2_service_iam_member" "orchestrator_public" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.orchestrator.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "orchestrator_url" {
  description = "URL of the Marathon Planner Agent Cloud Run service"
  value       = google_cloud_run_v2_service.orchestrator.uri
}

output "orchestrator_service_account" {
  description = "Service account used by Marathon Planner Agent"
  value       = google_service_account.orchestrator.email
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for Marathon Planner Agent images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.orchestrator.repository_id}"
}

output "orchestrator_a2a_endpoint" {
  description = "A2A endpoint for the Marathon Planner Agent"
  value       = "${google_cloud_run_v2_service.orchestrator.uri}/.well-known/agent.json"
}
