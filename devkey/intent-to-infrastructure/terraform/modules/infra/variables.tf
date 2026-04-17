variable "project_id" {}
variable "region" {}
variable "prefix" {}
variable "gpu_machine_type" {}
variable "gpu_accelerator_type" {}
variable "node_locations" {
  description = "List of zones for the GPU node pool"
  type        = list(string)
}