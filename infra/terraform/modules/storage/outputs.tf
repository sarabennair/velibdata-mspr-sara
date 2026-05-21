output "storage_account_id" {
  value = azurerm_storage_account.velibdata.id
}

output "storage_account_name" {
  value = azurerm_storage_account.velibdata.name
}

output "primary_dfs_endpoint" {
  description = "DFS endpoint — used by dbt teammate to configure Synapse linked service"
  value       = azurerm_storage_account.velibdata.primary_dfs_endpoint
}
