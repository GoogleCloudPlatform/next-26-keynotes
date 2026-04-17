output "frontend_ip" {
  description = "The internal IP address of the Gateway (used by runner route)"
  value       = try(data.kubernetes_resource.gateway.object.status.addresses[0].value, "")
}

output "gateway_resource" {
  description = "The Kubernetes Gateway resource"
  value       = try(data.kubernetes_resource.gateway.object, null)
}

output "vllm_deployment" {
  description = "The vLLM Kubernetes Deployment"
  value       = try(kubernetes_deployment.vllm[0].metadata[0].name, null)
}

output "gateway_forwarding_rule" {
  description = "The GCE Forwarding Rule associated with the Gateway"
  value       = try(data.kubernetes_resource.gateway.object.metadata.annotations["networking.gke.io/forwarding-rules"], null)
}