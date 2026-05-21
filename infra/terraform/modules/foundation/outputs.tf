output "resource_group_id" {
  value = azurerm_resource_group.velibdata.id
}

output "tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}

output "pipeline_sp_object_id" {
  value = azuread_service_principal.velibdata_pipeline.object_id
}

output "pipeline_sp_client_id" {
  value = azuread_application.velibdata_pipeline.client_id
}

output "key_vault_id" {
  value = azurerm_key_vault.velibdata.id
}

output "key_vault_name" {
  value = azurerm_key_vault.velibdata.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.velibdata.vault_uri
}
