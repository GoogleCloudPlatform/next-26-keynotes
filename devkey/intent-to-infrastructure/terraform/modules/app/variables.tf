variable "project_id" {}
variable "cluster_name" {}
variable "prefix" {
  description = "The environment prefix for resource naming."
  type        = string
}
variable "image_url" {
  description = "The full URL of the application image to deploy."
  type        = string
}
variable "app_version" {
  description = "The version of the app, to be passed as an env var."
  type        = string
  default     = "local"
}
variable "model_name" {}
variable "vllm_image" {}
variable "gpu_type" {}
variable "model_bucket_name" {}
variable "model_reader_sa_email" {}

variable "use_gemini_api" {
  description = "Whether to use the Vertex AI Gemini API instead of vLLM."
  type        = bool
  default     = false
}

variable "region" {
  description = "The GCP region (used for Vertex AI location)."
  type        = string
  default     = "asia-southeast1"
}

variable "gemini_model_name" {
  description = "The Gemini model name."
  type        = string
  default     = "gemini-3-flash-preview"
}

variable "enable_vllm" {
  description = "Whether to deploy the vLLM server."
  type        = bool
  default     = true
}

variable "enable_inference_gateway" {
  description = "Whether to configure HPA for GPU metrics (Inference Gateway pattern)."
  type        = bool
  default     = false
}

variable "lustre_mount_point" {
  description = "The mount point of the Lustre instance (e.g., /lustrefs). Empty string if Lustre is not active."
  type        = string
  default     = ""
}

variable "lustre_ip" {
  description = "The IP address of the Lustre instance. Empty string if Lustre is not active."
  type        = string
  default     = ""
}

variable "use_lustre" {
  description = "Whether vLLM should mount Lustre instead of GCSFuse."
  type        = bool
  default     = false
}

variable "hpa_target_cpu" {
  description = "Target CPU utilization percentage for the vLLM HPA."
  type        = number
  default     = 75
}

variable "hf_token" {
  description = "HuggingFace API token for downloading gated models (e.g., Gemma)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_otel" {
  description = "Whether to enable OpenTelemetry tracing (collector sidecar + env vars)."
  type        = bool
  default     = false
}

variable "lustre_copy_active" {
  description = "Set true to create PV/PVC, run copy job, then delete PV/PVC. Set false after copy is done."
  type        = bool
  default     = false
}

variable "model_subdir" {
  description = "GCS subdirectory (and Lustre path) where model weights are stored. Defaults to model_name when empty."
  type        = string
  default     = ""
}

variable "model_served_name" {
  description = "The --served-model-name passed to vLLM. Defaults to model_name when empty."
  type        = string
  default     = ""
}

variable "model_hf_repo" {
  description = "HuggingFace repo ID (e.g. google/gemma-4-E4B-it). When empty, auto-converted from model_name by replacing the first hyphen with a slash."
  type        = string
  default     = ""
}

variable "vllm_extra_args" {
  description = "Additional vLLM server args appended after standard args (e.g. [\"--enable-auto-tool-choice\", \"--tool-call-parser\", \"gemma4\"])."
  type        = list(string)
  default     = []
}