variable "subscription_id" { type = string }
variable "location" {
  type    = string
  default = "eastus2"
}
variable "resource_group_name" { type = string }
variable "tags" {
  type    = map(string)
  default = { environment = "lab", owner = "engineering", cost_center = "training", managed_by = "terraform" }
}

variable "storage_account_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Choose a globally unique 3-24-character lowercase storage account name."
  }
}

variable "registry_name" { type = string }
variable "repository_name" {
  type    = string
  default = "platform/app"
  validation {
    condition     = can(regex("^[a-z0-9]+([._/-][a-z0-9]+)*$", var.repository_name))
    error_message = "Use a lowercase repository path without spaces, quotes or condition-language characters."
  }
}
variable "enable_publisher" {
  type    = bool
  default = false
}
variable "github_oidc_subject" {
  type    = string
  default = ""
}
