output "resource_group_id" {
  value = azurerm_resource_group.velibdata.id
}

output "tenant_id" {
  value = data.azurerm_client_config.current.tenant_id
}

# Object ID of the currently logged-in user (az login session)
# Used for RBAC assignments on storage, Event Hubs, etc.
output "current_user_object_id" {
  value = data.azurerm_client_config.current.object_id
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
