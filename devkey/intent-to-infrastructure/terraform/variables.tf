# -------------------------------------------------------------------
# Hypercomputer – Variables
# -------------------------------------------------------------------

# --- Core Identity ---
variable "project_id" {
  description = "The Google Cloud Project ID."
  type        = string
}

variable "region" {
  description = "The Google Cloud region."
  type        = string
}

variable "env_prefix" {
  description = "The environment prefix for resource naming (e.g., hc-demo)."
  type        = string
}

variable "zone" {
  description = "The Google Cloud zone for zonal resources (e.g., Lustre)."
  type        = string
}

# --- GPU Configuration ---
variable "gpu_machine_type" {
  description = "The machine type for the GPU node pool."
  type        = string
}

variable "gpu_accelerator_type" {
  description = "The accelerator type for the GPU node pool."
  type        = string
}

variable "node_locations" {
  description = "List of zones for the GPU node pool."
  type        = list(string)
}

# --- Container Image ---
variable "image_url" {
  description = "The full container image URL for the chatbot. Defaults to asia-southeast1-docker.pkg.dev/<project_id>/devkey/chatbot."
  type        = string
  default     = ""
}

# --- App Configuration ---
variable "app_version" {
  description = "The application version tag."
  type        = string
}

variable "model_name" {
  description = "The name of the HuggingFace model to load."
  type        = string
}

variable "vllm_image" {
  description = "The container image for vLLM."
  type        = string
  default     = "vllm/vllm-openai:latest"
}

variable "use_gemini_api" {
  description = "Whether to use the Gemini API instead of vLLM."
  type        = bool
  default     = false
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

variable "vllm_hpa_target_cpu" {
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

variable "model_subdir" {
  description = "GCS subdirectory (and Lustre path) for model weights."
  type        = string
  default     = ""
}

variable "model_served_name" {
  description = "The --served-model-name for vLLM."
  type        = string
  default     = ""
}

variable "model_hf_repo" {
  description = "HuggingFace repo ID (e.g. google/gemma-4-E4B-it)."
  type        = string
  default     = ""
}

variable "vllm_extra_args" {
  description = "Additional vLLM server args."
  type        = list(string)
  default     = []
}

variable "enable_otel" {
  description = "Whether to enable OpenTelemetry tracing."
  type        = bool
  default     = false
}

# --- Lustre ---
variable "lustre_active" {
  description = "Whether to deploy the managed Lustre instance."
  type        = bool
  default     = false
}

variable "use_lustre" {
  description = "Whether to wire Lustre storage to vLLM (false = GCS, true = Lustre)."
  type        = bool
  default     = false
}

variable "lustre_copy_active" {
  description = "Whether to create PV/PVC and run copy job for Lustre."
  type        = bool
  default     = false
}

# --- Cloud Run Configuration ---
variable "cloud_run_image_url" {
  description = "The container image URL for the Cloud Run service."
  type        = string
  default     = ""
}

variable "cloud_run_service_name" {
  description = "The name of the Cloud Run service."
  type        = string
  default     = "chatbot"
}

variable "cloud_run_port" {
  description = "The port the Cloud Run container listens on."
  type        = number
  default     = 8207
}

# --- Module Activation Flags ---
variable "cloud_run_active" {
  description = "Whether to deploy the Cloud Run service."
  type        = bool
  default     = false
}

variable "traffic_active" {
  description = "Whether to deploy the traffic generator."
  type        = bool
  default     = false
}

variable "monitoring_active" {
  description = "Whether to deploy the monitoring dashboard."
  type        = bool
  default     = true
}

variable "app_active" {
  description = "Whether to deploy Kubernetes workloads (module.app). Set to false for step1 (infra-only provision), true for step2+."
  type        = bool
  default     = true
}

variable "create_alerts" {
  description = "Whether to create monitoring alert policies."
  type        = bool
  default     = false
}

# --- Traffic Configuration ---
variable "user_count" {
  description = "Number of Locust users per instance."
  type        = number
  default     = 100
}

variable "traffic_instance_count" {
  description = "Number of instances in the traffic generation MIG."
  type        = number
  default     = 1
}

variable "traffic_multiplier_low" {
  description = "Multiplier for baseline traffic load."
  type        = number
  default     = 1
}

variable "traffic_multiplier_high" {
  description = "Multiplier for peak traffic load."
  type        = number
  default     = 1
}

variable "baseline_users_min" {
  description = "Minimum baseline users for traffic generator."
  type        = number
  default     = 15
}

variable "baseline_users_max" {
  description = "Maximum baseline users for traffic generator."
  type        = number
  default     = 25
}

variable "peak_users_min" {
  description = "Minimum peak users for traffic generator."
  type        = number
  default     = 50
}

variable "peak_users_max" {
  description = "Maximum peak users for traffic generator."
  type        = number
  default     = 80
}

variable "min_wait" {
  description = "Minimum wait time between tasks in seconds."
  type        = number
  default     = 1
}

variable "max_wait" {
  description = "Maximum wait time between tasks in seconds."
  type        = number
  default     = 2
}

variable "ramp_up_pct" {
  description = "Percentage of cycle for ramp up phase."
  type        = number
  default     = 0.3
}

variable "peak_pct" {
  description = "Percentage of cycle for peak phase."
  type        = number
  default     = 0.2
}

variable "ramp_down_pct" {
  description = "Percentage of cycle for ramp down phase."
  type        = number
  default     = 0.1
}
