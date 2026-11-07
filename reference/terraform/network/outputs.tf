output "resource_group_name" {
  value = azurerm_resource_group.network_nonproduction.name
}

output "location" {
  value = azurerm_resource_group.network_nonproduction.location
}

output "virtual_network_id" {
  value = azurerm_virtual_network.app_nonproduction.id
}

output "virtual_network_name" {
  value = azurerm_virtual_network.app_nonproduction.name
}

output "functions_subnet_id" {
  value = azurerm_subnet.functions_integration.id
}

output "private_endpoints_subnet_id" {
  value = azurerm_subnet.private_endpoints.id
}
