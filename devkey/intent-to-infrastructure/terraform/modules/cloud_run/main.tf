# Enable Cloud Run API
resource "google_project_service" "run_api" {
  project            = var.project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# Create a dedicated service account for the Runner
resource "google_service_account" "runner_sa" {
  account_id   = "${var.env_prefix}-runner-sa"
  display_name = "Runner Agent Service Account for ${var.env_prefix}"
  project      = var.project_id
}

resource "google_cloud_run_v2_service" "runner" {
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
    service_account = google_service_account.runner_sa.email
  }

  # Ensure API is enabled before creating the service
  depends_on = [google_project_service.run_api]
}

# Allow unauthenticated invocations
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = google_cloud_run_v2_service.runner.name
  location = google_cloud_run_v2_service.runner.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Grant Vertex AI User to the dedicated service account
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.runner_sa.email}"
}
