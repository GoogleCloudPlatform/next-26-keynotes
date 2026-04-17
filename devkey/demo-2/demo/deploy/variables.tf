# Variables for the demo deployment
# Deploys two Cloud Run services (solo + full_team) from the same image

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "image" {
  description = "Container image for Marathon Planner Agent (full Artifact Registry path with tag)"
  type        = string
}

# Service account to use for both demo services
variable "service_account_email" {
  description = "Service account email for the Cloud Run services (reuse from main deployment)"
  type        = string
}

# Agent Engine resource names
variable "evaluator_agent_resource_name" {
  description = "Resource name of deployed Evaluator Agent"
  type        = string
}

variable "simulator_agent_resource_name" {
  description = "Resource name of deployed Simulation Controller Agent"
  type        = string
}
