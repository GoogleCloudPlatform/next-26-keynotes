variable "project_id" {
  description = "The project ID to host the dashboard in."
  type        = string
}

variable "cluster_name" {
  description = "The name of the GKE cluster to monitor."
  type        = string
}

variable "env_prefix" {
  description = "The environment prefix for resource naming (e.g., hypercomputer-w1)."
  type        = string
}

variable "create_alerts" {
  description = "Whether to create alert policies. Set to false if Prometheus metrics are not yet available."
  type        = bool
  default     = false
}
