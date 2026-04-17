variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud Region"
  type        = string
  default     = "asia-southeast1"
}

variable "image_url" {
  description = "URL of the container image to deploy"
  type        = string
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "runner-agent"
}

variable "port" {
  description = "Port the container listens on"
  type        = number
  default     = 8207
}

variable "env_prefix" {
  description = "Prefix for resources to avoid conflicts"
  type        = string
}

variable "use_gemini_api" {
  description = "Whether to use Gemini API instead of vLLM"
  type        = bool
  default     = true
}
