# -------------------------------------------------------------------
# Environment: demo – Step 1 (Setup)
# -------------------------------------------------------------------
# Foundation: APIs, VPC, GKE, GCS, monitoring dashboard.
# No model download, no vLLM, no traffic, no Lustre.
# -------------------------------------------------------------------

# Core Identity
region     = "asia-southeast1"
env_prefix = "hc-demo"
zone       = "asia-southeast1-a"

# GPU Configuration
gpu_machine_type     = "g2-standard-12"
gpu_accelerator_type = "nvidia-l4"
node_locations       = ["asia-southeast1-a", "asia-southeast1-b", "asia-southeast1-c"]

# App Configuration
app_version         = "v1.10"
model_name          = "google-gemma-4-E4B-it"
model_subdir        = "gemma-4-e4b-it-weights"
model_served_name   = "gemma-4-E4B-it"
model_hf_repo       = "google/gemma-4-E4B-it"
vllm_image          = "vllm/vllm-openai:gemma4"
vllm_extra_args     = ["--enable-auto-tool-choice", "--tool-call-parser", "gemma4", "--gpu-memory-utilization", "0.9"]
use_gemini_api      = true
enable_vllm         = false
gemini_model_name   = "gemini-2.5-flash"
vllm_hpa_target_cpu = 50

enable_inference_gateway = false
cloud_run_port = 8080

# Storage
lustre_active      = false
use_lustre         = false
lustre_copy_active = false

# Module Activation
traffic_active    = false
monitoring_active = true
app_active        = false   # No K8s workloads in step1 — cluster provisions first
create_alerts     = false
cloud_run_active  = true

# Traffic Configuration (inactive, but set explicitly)
traffic_multiplier_low  = 0.05
traffic_multiplier_high = 10
user_count              = 300
baseline_users_min      = 3
baseline_users_max      = 6
peak_users_min          = 50
peak_users_max          = 80
min_wait                = 0.1
max_wait                = 0.3
traffic_instance_count  = 1
ramp_up_pct             = 0.15
peak_pct                = 0.5
ramp_down_pct           = 0.0
