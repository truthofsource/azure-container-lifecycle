mock_provider "azurerm" {}
mock_provider "azapi" {}
variables {
  subscription_id      = "00000000-0000-0000-0000-000000000001"
  resource_group_name  = "rg-example-delivery"
  storage_account_name = "stexampleartifacts001"
  registry_name        = "acrexampleartifacts001"
}
run "no_publisher_and_no_storage_key" {
  command = plan
  assert {
    condition     = length(azurerm_user_assigned_identity.publisher) == 0
    error_message = "Publisher grants must remain off by default."
  }
  assert {
    condition     = !azurerm_storage_account.data.shared_access_key_enabled && !azurerm_container_registry.images.admin_enabled
    error_message = "Registry admin and storage shared-key access must remain off."
  }
}
run "publisher_needs_exact_trust" {
  command = plan
  variables { enable_publisher = true }
  expect_failures = [azurerm_federated_identity_credential.publisher[0]]
}
