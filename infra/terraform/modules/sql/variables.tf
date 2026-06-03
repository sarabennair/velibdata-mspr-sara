variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
}

variable "location" {
  description = "Azure region for SQL resources"
  type        = string
}

variable "key_vault_id" {
  description = "Key Vault ID where SQL connection secrets are stored"
  type        = string
}

variable "sql_server_name" {
  description = "Globally unique Azure SQL Server name"
  type        = string
}

variable "sql_database_name" {
  description = "Azure SQL Database name"
  type        = string
}

variable "sql_admin_login" {
  description = "Azure SQL administrator login"
  type        = string
  default     = "velibadmin"
}

variable "sql_sku_name" {
  description = "Azure SQL Database SKU. Basic is the lowest-cost DTU option suitable for Azure for Students demos."
  type        = string
  default     = "Basic"
}

variable "sql_max_size_gb" {
  description = "Maximum database size in GB"
  type        = number
  default     = 2
}

variable "sql_public_network_access_enabled" {
  description = "Whether public network access is enabled for the SQL server"
  type        = bool
  default     = true
}

variable "sql_allow_azure_services" {
  description = "Allow Azure services and resources to access this SQL server"
  type        = bool
  default     = true
}
