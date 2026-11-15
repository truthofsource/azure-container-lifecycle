resource "azurerm_container_registry" "images" {
  name                          = var.registry_name
  resource_group_name           = azurerm_resource_group.lab.name
  location                      = var.location
  sku                           = "Basic"
  admin_enabled                 = false
  public_network_access_enabled = true
  role_assignment_mode          = "AbacRepositoryPermissions"
  tags                          = var.tags
}
resource "azurerm_user_assigned_identity" "publisher" {
  count               = var.enable_publisher ? 1 : 0
  name                = "id-example-registry-publisher"
  resource_group_name = azurerm_resource_group.lab.name
  location            = var.location
  tags                = var.tags
}
resource "azurerm_federated_identity_credential" "publisher" {
  count                     = var.enable_publisher ? 1 : 0
  name                      = "github-reviewed-publisher"
  user_assigned_identity_id = azurerm_user_assigned_identity.publisher[0].id
  issuer                    = "https://token.actions.githubusercontent.com"
  audience                  = ["api://AzureADTokenExchange"]
  subject                   = var.github_oidc_subject
  lifecycle {
    precondition {
      condition     = length(trimspace(var.github_oidc_subject)) > 0 && !strcontains(var.github_oidc_subject, "*")
      error_message = "Set an exact reviewed OIDC subject before granting publisher access."
    }
  }
}
resource "azurerm_role_assignment" "repository_writer" {
  count                = var.enable_publisher ? 1 : 0
  scope                = azurerm_container_registry.images.id
  principal_id         = azurerm_user_assigned_identity.publisher[0].principal_id
  principal_type       = "ServicePrincipal"
  role_definition_name = "Container Registry Repository Writer"
  condition_version    = "2.0"
  condition            = <<-CONDITION
    (
      (
        !(ActionMatches{'Microsoft.ContainerRegistry/registries/repositories/metadata/read'})
        AND !(ActionMatches{'Microsoft.ContainerRegistry/registries/repositories/content/read'})
        AND !(ActionMatches{'Microsoft.ContainerRegistry/registries/repositories/metadata/write'})
        AND !(ActionMatches{'Microsoft.ContainerRegistry/registries/repositories/content/write'})
      )
      OR
      (@Request[Microsoft.ContainerRegistry/registries/repositories:name] StringEqualsIgnoreCase '${var.repository_name}')
    )
  CONDITION
}
output "registry_login_server" { value = azurerm_container_registry.images.login_server }
