# ============================================================
# Outputs — shared with dbt teammate and CI/CD
# Run: terraform output  to see all values after apply
# ============================================================

output "resource_group_name" {
  description = "Resource group containing all VélibData Azure resources"
  value       = var.resource_group_name
}

output "storage_account_name" {
  description = "ADLS Gen2 storage account name — give this to dbt teammate"
  value       = module.storage.storage_account_name
}

output "storage_account_id" {
  description = "ADLS Gen2 storage account resource ID"
  value       = module.storage.storage_account_id
}

output "bronze_container_name" {
  description = "Bronze layer container name"
  value       = "bronze"
}

output "silver_container_name" {
  description = "Silver layer container name — dbt teammate writes here"
  value       = "silver"
}

output "gold_container_name" {
  description = "Gold layer container name — dbt teammate writes here"
  value       = "gold"
}

output "key_vault_name" {
  description = "Key Vault name — all secrets stored here"
  value       = module.foundation.key_vault_name
}

output "key_vault_uri" {
  description = "Key Vault URI — used in Python code and dbt profile"
  value       = module.foundation.key_vault_uri
}

output "eventhub_namespace_name" {
  description = "Event Hubs namespace name"
  value       = var.eventhub_namespace_name
}

output "sql_server_name" {
  description = "Azure SQL Server name"
  value       = module.sql.sql_server_name
}

output "sql_server_fqdn" {
  description = "Azure SQL Server fully qualified domain name"
  value       = module.sql.sql_server_fqdn
}

output "sql_database_name" {
  description = "Azure SQL Database name"
  value       = module.sql.sql_database_name
}

output "sql_admin_login" {
  description = "Azure SQL administrator login"
  value       = module.sql.sql_admin_login
}

output "sql_connection_string" {
  description = "Azure SQL connection string stored in Key Vault as sql-connection-string"
  value       = module.sql.sql_connection_string
  sensitive   = true
}

output "adf_name" {
  description = "Azure Data Factory name"
  value       = var.adf_name
}

output "app_insights_instrumentation_key" {
  description = "Application Insights key — used in Python logging"
  value       = module.monitoring.app_insights_instrumentation_key
  sensitive   = true
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID — used for dbt Cloud logging (give to teammate)"
  value       = module.monitoring.log_analytics_workspace_id
}
