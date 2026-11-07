resource "azurerm_resource_group" "network_nonproduction" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

resource "azurerm_virtual_network" "app_nonproduction" {
  name                = var.virtual_network_name
  resource_group_name = azurerm_resource_group.network_nonproduction.name
  location            = azurerm_resource_group.network_nonproduction.location

  address_space = var.address_space

  tags = var.tags
}

resource "azurerm_subnet" "functions_integration" {
  name                 = var.functions_subnet_name
  resource_group_name  = azurerm_resource_group.network_nonproduction.name
  virtual_network_name = azurerm_virtual_network.app_nonproduction.name

  address_prefixes  = var.functions_subnet_prefixes
  service_endpoints = var.functions_subnet_service_endpoints

  delegation {
    name = "delegation-functions-flex-consumption"

    service_delegation {
      name = "Microsoft.App/environments"

      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }
}

resource "azurerm_subnet" "private_endpoints" {
  name                 = var.private_endpoints_subnet_name
  resource_group_name  = azurerm_resource_group.network_nonproduction.name
  virtual_network_name = azurerm_virtual_network.app_nonproduction.name

  address_prefixes = var.private_endpoints_subnet_prefixes
}
