output "adf_id" {
  value = azurerm_data_factory.velibdata.id
}

output "adf_name" {
  value = azurerm_data_factory.velibdata.name
}

output "adf_managed_identity_object_id" {
  value = azurerm_data_factory.velibdata.identity[0].principal_id
}
