output "sql_server_id" {
  description = "Azure SQL Server resource ID"
  value       = azurerm_mssql_server.velibdata.id
}

output "sql_server_name" {
  description = "Azure SQL Server name"
  value       = azurerm_mssql_server.velibdata.name
}

output "sql_server_fqdn" {
  description = "Azure SQL Server fully qualified domain name"
  value       = azurerm_mssql_server.velibdata.fully_qualified_domain_name
}

output "sql_database_id" {
  description = "Azure SQL Database resource ID"
  value       = azurerm_mssql_database.velibdata.id
}

output "sql_database_name" {
  description = "Azure SQL Database name"
  value       = azurerm_mssql_database.velibdata.name
}

output "sql_admin_login" {
  description = "Azure SQL administrator login"
  value       = var.sql_admin_login
}

output "sql_connection_string" {
  description = "Azure SQL connection string"
  value = format(
    "Server=tcp:%s,1433;Initial Catalog=%s;Persist Security Info=False;User ID=%s;Password=%s;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;",
    azurerm_mssql_server.velibdata.fully_qualified_domain_name,
    azurerm_mssql_database.velibdata.name,
    var.sql_admin_login,
    random_password.sql_admin.result
  )
  sensitive = true
}
