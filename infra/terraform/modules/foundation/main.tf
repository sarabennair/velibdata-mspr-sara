data "azurerm_client_config" "current" {}
data "azuread_client_config" "current" {}

# ── Resource Group ────────────────────────────────────────────
resource "azurerm_resource_group" "velibdata" {
  name     = var.resource_group_name
  location = var.location
}

# ── Service Principal (pipeline identity) ────────────────────
resource "azuread_application" "velibdata_pipeline" {
  display_name = "velibdata-pipeline-sp"
}

resource "azuread_service_principal" "velibdata_pipeline" {
  client_id = azuread_application.velibdata_pipeline.client_id
}

resource "azuread_service_principal_password" "velibdata_pipeline" {
  service_principal_id = azuread_service_principal.velibdata_pipeline.id
  end_date             = "2027-01-01T00:00:00Z"
}

# ── Key Vault ─────────────────────────────────────────────────
resource "azurerm_key_vault" "velibdata" {
  name                       = var.key_vault_name
  location                   = azurerm_resource_group.velibdata.location
  resource_group_name        = azurerm_resource_group.velibdata.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
}

# Your personal admin access to Key Vault
resource "azurerm_key_vault_access_policy" "admin" {
  key_vault_id = azurerm_key_vault.velibdata.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge", "Recover"]
}

# Pipeline SP: read-only access to secrets (CdC §8.5 — HIGH Critique)
resource "azurerm_key_vault_access_policy" "pipeline_sp" {
  key_vault_id = azurerm_key_vault.velibdata.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azuread_service_principal.velibdata_pipeline.object_id

  secret_permissions = ["Get", "List"]

  depends_on = [azurerm_key_vault_access_policy.admin]
}

# ── Store SP credentials in Key Vault ────────────────────────
resource "azurerm_key_vault_secret" "sp_client_id" {
  name         = "pipeline-sp-client-id"
  value        = azuread_application.velibdata_pipeline.client_id
  key_vault_id = azurerm_key_vault.velibdata.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

resource "azurerm_key_vault_secret" "sp_client_secret" {
  name         = "pipeline-sp-client-secret"
  value        = azuread_service_principal_password.velibdata_pipeline.value
  key_vault_id = azurerm_key_vault.velibdata.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}

resource "azurerm_key_vault_secret" "tenant_id" {
  name         = "azure-tenant-id"
  value        = data.azurerm_client_config.current.tenant_id
  key_vault_id = azurerm_key_vault.velibdata.id
  depends_on   = [azurerm_key_vault_access_policy.admin]
}
