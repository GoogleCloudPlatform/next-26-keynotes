# -------------------------------------------------------------------
# Hypercomputer – Outputs
# -------------------------------------------------------------------

# --- Infra ---
output "cluster_name" {
  description = "The name of the GKE cluster."
  value       = module.infra.cluster_name
}

output "cluster_endpoint" {
  description = "The endpoint of the GKE cluster."
  value       = module.infra.cluster_endpoint
}

output "network_name" {
  description = "The name of the VPC network."
  value       = module.infra.network_name
}

output "model_bucket_name" {
  description = "The name of the GCS model bucket."
  value       = module.infra.model_bucket_name
}

output "model_bucket_url" {
  description = "The URL of the GCS model bucket."
  value       = module.infra.model_bucket_url
}

# --- App ---
output "chat_endpoint" {
  description = "The internal IP address of the Chatbot Gateway."
  value       = try(module.app[0].frontend_ip, "")
}

output "vllm_deployment" {
  description = "The name of the vLLM Deployment."
  value       = try(module.app[0].vllm_deployment, null)
}





# --- Monitoring ---
output "monitoring_dashboard_url" {
  description = "The URL of the Cloud Monitoring Dashboard."
  value       = try("https://console.cloud.google.com/monitoring/dashboards/builder/${element(split("/", module.monitoring[0].dashboard_id), 3)}?project=${var.project_id}", "")
}

# --- Cloud Run ---
output "cloud_run_url" {
  description = "The URL of the Cloud Run service."
  value       = try(module.cloud_run[0].service_url, "")
}
