variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "eventhub_namespace_name" { type = string }
variable "key_vault_id" { type = string }
variable "capture_storage_account_id" { type = string }
variable "capture_container_name" { type = string }

variable "capture_interval_in_seconds" {
  type    = number
  default = 900
}

variable "capture_size_limit_in_bytes" {
  type    = number
  default = 10485760
}
