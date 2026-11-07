terraform {
  required_version = ">= 1.7.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "= 4.81.0" }
  }
}
provider "azurerm" {
  features {}
}
variable "enable_example" {
  type    = bool
  default = false
}
variable "environment_id" {
  type    = string
  default = "/subscriptions/00000000-0000-4000-8000-000000000000/resourceGroups/rg-example/providers/Microsoft.App/managedEnvironments/cae-example"
}
variable "pull_identity_id" {
  type    = string
  default = "/subscriptions/00000000-0000-4000-8000-000000000000/resourceGroups/rg-example/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-example-worker"
}
variable "image_digest" {
  type    = string
  default = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "Select an exact registry digest; a mutable tag is not accepted."
  }
}
resource "azurerm_container_app_job" "example" {
  count                        = var.enable_example ? 1 : 0
  name                         = "job-example-carebridge"
  location                     = "centralus"
  resource_group_name          = "rg-example-workers"
  container_app_environment_id = var.environment_id
  replica_timeout_in_seconds   = 840
  replica_retry_limit          = 0
  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }
  identity {
    type         = "UserAssigned"
    identity_ids = [var.pull_identity_id]
  }
  registry {
    server   = "exampleregistry.azurecr.io"
    identity = var.pull_identity_id
  }
  template {
    container {
      name    = "carebridge-example"
      image   = "exampleregistry.azurecr.io/carebridge/importer@${var.image_digest}"
      cpu     = 1
      memory  = "2Gi"
      command = ["node"]
      args    = ["src/demo.mjs"]
      env {
        name  = "CAREBRIDGE_WORKER_ENABLED"
        value = "false"
      }
    }
  }
}
output "job_id" { value = try(azurerm_container_app_job.example[0].id, null) }
