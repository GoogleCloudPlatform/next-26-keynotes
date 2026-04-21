# -------------------------------------------------------------------
# Hypercomputer – Single Root Module
# -------------------------------------------------------------------
# All infrastructure and application resources in one module.
# Steps 1–4 are different tfvars applied to this module.
# -------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  backend "gcs" {
    # Partial config – bucket and prefix injected via:
    #   terraform init \
    #     -backend-config="bucket=<BUCKET>" \
    #     -backend-config="prefix=terraform/state/<ENV>"
  }
}

# -------------------------------------------------------------------
# Providers
# -------------------------------------------------------------------
provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  effective_image_url = var.image_url != "" ? var.image_url : "asia-southeast1-docker.pkg.dev/${var.project_id}/chatbot-repo/chatbot"
  effective_cloud_run_image_url = var.cloud_run_image_url != "" ? var.cloud_run_image_url : "asia-southeast1-docker.pkg.dev/${var.project_id}/chatbot-repo/chatbot:latest"
}

# Kubernetes provider uses kubeconfig populated by deploy.sh after GKE cluster is created.
# On step1 (app_active=false), no K8s resources are evaluated so this is safe
# even if the kubeconfig file doesn't exist yet.
provider "kubernetes" {
  config_path = pathexpand("~/.kube/config")
}

# -------------------------------------------------------------------
# Module: infra (VPC, GKE, GCS, Service Accounts)
# -------------------------------------------------------------------
module "infra" {
  source               = "./modules/infra"
  project_id           = var.project_id
  region               = var.region
  prefix               = var.env_prefix
  gpu_machine_type     = var.gpu_machine_type
  gpu_accelerator_type = var.gpu_accelerator_type
  node_locations       = var.node_locations
}



# -------------------------------------------------------------------
# Module: app (K8s Deployments – Chatbot, vLLM, Gateway, HPA)
# -------------------------------------------------------------------
module "app" {
  count  = var.app_active ? 1 : 0
  source = "./modules/app"

  project_id            = var.project_id
  cluster_name          = module.infra.cluster_name
  prefix                = var.env_prefix
  image_url             = local.effective_image_url
  app_version           = var.app_version
  model_name            = var.model_name
  vllm_image            = var.vllm_image
  gpu_type              = module.infra.gpu_type
  model_bucket_name     = module.infra.model_bucket_name
  model_reader_sa_email = module.infra.model_reader_sa_email
  agent_sa_email        = module.infra.agent_sa_email

  use_gemini_api           = var.use_gemini_api
  gemini_model_name        = var.gemini_model_name
  region                   = var.region
  enable_vllm              = var.enable_vllm
  enable_inference_gateway = var.enable_inference_gateway
  hpa_target_cpu           = var.vllm_hpa_target_cpu
  hf_token                 = var.hf_token
  model_subdir             = var.model_subdir
  model_served_name        = var.model_served_name
  model_hf_repo            = var.model_hf_repo
  vllm_extra_args          = var.vllm_extra_args

  enable_otel        = var.enable_otel

  depends_on = [module.infra]
}

# -------------------------------------------------------------------
# Module: cloud_run (Cloud Run Service for Chatbot)
# -------------------------------------------------------------------
module "cloud_run" {
  count  = var.cloud_run_active ? 1 : 0
  source = "./modules/cloud_run"

  project_id   = var.project_id
  region       = var.region
  env_prefix   = var.env_prefix
  image_url    = local.effective_cloud_run_image_url
  service_name = var.cloud_run_service_name
  port         = var.cloud_run_port
  use_gemini_api = var.use_gemini_api
  agent_sa_email = module.infra.agent_sa_email
}



# -------------------------------------------------------------------
# Module: monitoring (Cloud Monitoring Dashboard)
# -------------------------------------------------------------------
module "monitoring" {
  count  = var.monitoring_active ? 1 : 0
  source = "./modules/monitoring"

  project_id    = var.project_id
  cluster_name  = module.infra.cluster_name
  env_prefix    = var.env_prefix
  create_alerts = var.create_alerts
}
