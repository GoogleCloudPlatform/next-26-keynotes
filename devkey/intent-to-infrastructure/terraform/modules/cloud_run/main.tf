# Enable Cloud Run API
resource "google_project_service" "run_api" {
  project            = var.project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}



resource "google_cloud_run_v2_service" "agent" {
  name                = "${var.env_prefix}-${var.service_name}"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    containers {
      image = var.image_url
      ports {
        container_port = var.port
      }
      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "USE_GEMINI_API"
        value = tostring(var.use_gemini_api)
      }
    }
    service_account = var.agent_sa_email
  }

  # Ensure API is enabled before creating the service
  depends_on = [google_project_service.run_api]
}

# Allow unauthenticated invocations
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.agent.name
  location = google_cloud_run_v2_service.agent.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}


