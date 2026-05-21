variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "rg-velibdata"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "francecentral"
}

variable "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account (must be globally unique, lowercase, 3-24 chars)"
  type        = string
  default     = "velibdatastorage"
}

variable "key_vault_name" {
  description = "Name of the Azure Key Vault (must be globally unique, 3-24 chars)"
  type        = string
  default     = "kv-velibdata"
}

variable "eventhub_namespace_name" {
  description = "Name of the Event Hubs namespace"
  type        = string
  default     = "evhns-velibdata"
}

variable "adf_name" {
  description = "Name of the Azure Data Factory instance"
  type        = string
  default     = "adf-velibdata"
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
  default     = "2025-09-01T00:00:00Z"
}
