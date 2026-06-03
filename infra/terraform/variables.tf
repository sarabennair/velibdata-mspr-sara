variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-velibdata"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "germanywestcentral"
}

variable "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account (must be globally unique, lowercase, 3-24 chars)"
  type        = string
  default     = "velibdata1c53"
}

variable "key_vault_name" {
  description = "Name of the Azure Key Vault (must be globally unique, 3-24 chars)"
  type        = string
  default     = "kv-velib-1c53"
}

variable "eventhub_namespace_name" {
  description = "Name of the Event Hubs namespace"
  type        = string
  default     = "evhns-velib-1c53"
}

variable "eventhub_capture_container_name" {
  description = "ADLS Gen2 filesystem/container used by Event Hubs Capture"
  type        = string
  default     = "bronze"
}

variable "eventhub_capture_interval_in_seconds" {
  description = "Event Hubs Capture interval in seconds. 900 seconds keeps archive frequency low for Azure for Students."
  type        = number
  default     = 900
}

variable "eventhub_capture_size_limit_in_bytes" {
  description = "Event Hubs Capture size limit in bytes before an archive is emitted"
  type        = number
  default     = 10485760
}

variable "adf_name" {
  description = "Name of the Azure Data Factory instance"
  type        = string
  default     = "adf-velib-1c53"
}

variable "sql_server_name" {
  description = "Globally unique Azure SQL Server name (lowercase, 3-63 chars)"
  type        = string
  default     = "sql-velib-1c53"
}

variable "sql_database_name" {
  description = "Azure SQL Database name used for Bronze, Silver, and Gold schemas"
  type        = string
  default     = "sqldb-velibdata"
}

variable "sql_admin_login" {
  description = "Azure SQL administrator login"
  type        = string
  default     = "velibadmin"
}

variable "sql_sku_name" {
  description = "Economical Azure SQL Database SKU compatible with Azure for Students demos"
  type        = string
  default     = "Basic"
}

variable "sql_max_size_gb" {
  description = "Maximum Azure SQL Database size in GB"
  type        = number
  default     = 2
}

variable "sql_public_network_access_enabled" {
  description = "Whether public network access is enabled for the Azure SQL Server"
  type        = bool
  default     = true
}

variable "sql_allow_azure_services" {
  description = "Allow Azure services and resources to access this Azure SQL Server"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for Azure Monitor and budget alerts"
  type        = string
}

variable "budget_amount" {
  description = "Monthly budget in USD (Azure for Students = $100)"
  type        = number
  default     = 100
}

variable "budget_start_date" {
  description = "Start date for budget tracking (format: YYYY-MM-01T00:00:00Z)"
  type        = string
  default     = "2026-05-01T00:00:00Z"
}
