# Demo deployment: two Cloud Run services from the same image
#
# - marathon-planner-solo: Evaluator only (no Simulation Controller)
# - marathon-planner-full: Evaluator + Simulation Controller
#
# Uses the same image and service account as the main deployment.

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================================================
# SHARED LOCALS
# ============================================================================

locals {
  base_env = {
    GOOGLE_CLOUD_PROJECT      = var.project_id
    GOOGLE_CLOUD_LOCATION     = var.region
    GOOGLE_GENAI_USE_VERTEXAI = "true"
  }
}

# ============================================================================
# SOLO SERVICE — Evaluator only, no Simulation Controller
# ============================================================================

resource "google_cloud_run_v2_service" "solo" {
  name     = "marathon-planner-solo"
  location = var.region

  deletion_protection = false

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8080
      }

      # Base env vars
      dynamic "env" {
        for_each = local.base_env
        content {
          name  = env.key
          value = env.value
        }
      }

      # Solo mode: evaluator only
      env {
        name  = "EVALUATOR_AGENT_RESOURCE_NAME"
        value = var.evaluator_agent_resource_name
      }

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

    timeout = "600s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    purpose = "demo-solo"
    demo    = "next26"
  }
}

# Allow unauthenticated access to solo service
resource "google_cloud_run_v2_service_iam_member" "solo_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.solo.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================================
# FULL TEAM SERVICE — Evaluator + Simulation Controller
# ============================================================================

resource "google_cloud_run_v2_service" "full" {
  name     = "marathon-planner-full"
  location = var.region

  deletion_protection = false

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8080
      }

      # Base env vars
      dynamic "env" {
        for_each = local.base_env
        content {
          name  = env.key
          value = env.value
        }
      }

      # Full team mode: evaluator + simulation controller
      env {
        name  = "EVALUATOR_AGENT_RESOURCE_NAME"
        value = var.evaluator_agent_resource_name
      }

      env {
        name  = "SIMULATOR_AGENT_RESOURCE_NAME"
        value = var.simulator_agent_resource_name
      }

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

    timeout = "600s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    purpose = "demo-full"
    demo    = "next26"
  }
}

# Allow unauthenticated access to full service
resource "google_cloud_run_v2_service_iam_member" "full_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.full.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "solo_url" {
  description = "URL of the solo (evaluator-only) Marathon Planner service"
  value       = google_cloud_run_v2_service.solo.uri
}

output "full_url" {
  description = "URL of the full-team Marathon Planner service"
  value       = google_cloud_run_v2_service.full.uri
}

output "solo_a2a_endpoint" {
  description = "A2A agent card endpoint for solo service"
  value       = "${google_cloud_run_v2_service.solo.uri}/.well-known/agent.json"
}

output "full_a2a_endpoint" {
  description = "A2A agent card endpoint for full-team service"
  value       = "${google_cloud_run_v2_service.full.uri}/.well-known/agent.json"
}
