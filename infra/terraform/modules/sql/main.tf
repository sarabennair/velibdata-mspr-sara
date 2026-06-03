terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_password" "sql_admin" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "azurerm_mssql_server" "velibdata" {
  name                         = var.sql_server_name
  resource_group_name          = var.resource_group_name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_login
  administrator_login_password = random_password.sql_admin.result
  minimum_tls_version          = "1.2"

  public_network_access_enabled = var.sql_public_network_access_enabled
}

resource "azurerm_mssql_database" "velibdata" {
  name           = var.sql_database_name
  server_id      = azurerm_mssql_server.velibdata.id
  sku_name       = var.sql_sku_name
  max_size_gb    = var.sql_max_size_gb
  zone_redundant = false
}

resource "azurerm_mssql_firewall_rule" "allow_azure_services" {
  count            = var.sql_allow_azure_services ? 1 : 0
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.velibdata.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

resource "azurerm_key_vault_secret" "sql_server_name" {
  name         = "sql-server-name"
  value        = azurerm_mssql_server.velibdata.name
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "sql_database_name" {
  name         = "sql-database-name"
  value        = azurerm_mssql_database.velibdata.name
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "sql_admin_login" {
  name         = "sql-admin-login"
  value        = var.sql_admin_login
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "sql_admin_password" {
  name         = "sql-admin-password"
  value        = random_password.sql_admin.result
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "sql_connection_string" {
  name = "sql-connection-string"
  value = format(
    "Server=tcp:%s,1433;Initial Catalog=%s;Persist Security Info=False;User ID=%s;Password=%s;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;",
    azurerm_mssql_server.velibdata.fully_qualified_domain_name,
    azurerm_mssql_database.velibdata.name,
    var.sql_admin_login,
    random_password.sql_admin.result
  )
  key_vault_id = var.key_vault_id
}
