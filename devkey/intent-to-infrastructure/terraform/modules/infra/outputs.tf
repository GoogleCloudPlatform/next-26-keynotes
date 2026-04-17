output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "cluster_ca_certificate" {
  value = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
}

output "gpu_type" {
  value = "nvidia-l4"
}

output "model_bucket_name" {
  value = google_storage_bucket.models.name
}

output "model_reader_sa_email" {
  value = google_service_account.model_reader.email
}

output "model_bucket_url" {
  value = google_storage_bucket.models.url
}

output "network_name" {
  description = "The name of the VPC network created for this workspace."
  value       = google_compute_network.vpc.name
}

output "shared_model_bucket_url" {
  description = "The URL of the shared model bucket (only available if created in this workspace)."
  value       = try(google_storage_bucket.shared_models[0].url, null)
}