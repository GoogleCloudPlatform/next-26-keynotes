resource "google_project_service" "enabled_apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "servicenetworking.googleapis.com",
    "parallelstore.googleapis.com",
    "lustre.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "aiplatform.googleapis.com",
    "geminicloudassist.googleapis.com"
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# GCP APIs take ~60s to propagate after enablement.
# This sleep prevents race conditions (e.g. "Compute Engine API not ready")
# when Terraform immediately tries to create network resources.
resource "time_sleep" "api_propagation" {
  create_duration = "30s"
  depends_on      = [google_project_service.enabled_apis]
}

resource "google_storage_bucket" "shared_models" {
  # Only create this bucket in the c2 workspace to act as a shared repository
  # and avoid name conflicts with other workspaces.
  count                       = var.prefix == "hypercomputer-c2" ? 1 : 0
  name                        = "gemma-3-models-${var.project_id}"
  location                    = "US"
  uniform_bucket_level_access = true
}