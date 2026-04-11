# Terraform configuration for Strategy Analyst Agent infrastructure
# Creates GCS bucket for Vertex AI Eval and grants necessary permissions

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

# Variables
variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  # Set in terraform.tfvars
}

variable "project_number" {
  description = "Google Cloud Project Number"
  type        = string
  # Set in terraform.tfvars
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "Name of the GCS bucket for agent staging"
  type        = string
  # Set in terraform.tfvars
}

# GCS Bucket for Agent Staging and Vertex AI Eval
resource "google_storage_bucket" "agent_staging" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = false
  }

  lifecycle_rule {
    condition {
      age = 30  # Delete objects after 30 days
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    purpose = "agent-staging"
    demo    = "next26"
  }
}

# Grant Agent Engine service account access to the bucket
# This is required for Vertex AI Eval to write evaluation results
resource "google_storage_bucket_iam_member" "agent_engine_storage_admin" {
  bucket = google_storage_bucket.agent_staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:service-${var.project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

# Grant Discovery Engine service account access (for Gemini Enterprise)
resource "google_storage_bucket_iam_member" "discovery_engine_storage_viewer" {
  bucket = google_storage_bucket.agent_staging.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:service-${var.project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

# Grant Agent Engine service account AI Platform User role
# This is required for Vertex AI Eval to create evaluation items
resource "google_project_iam_member" "agent_engine_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:service-${var.project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

# Outputs
output "bucket_name" {
  description = "The name of the created GCS bucket"
  value       = google_storage_bucket.agent_staging.name
}

output "bucket_uri" {
  description = "The GCS URI for the bucket"
  value       = "gs://${google_storage_bucket.agent_staging.name}"
}

output "agent_engine_service_account" {
  description = "The Agent Engine service account that has been granted access"
  value       = "service-${var.project_number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}
