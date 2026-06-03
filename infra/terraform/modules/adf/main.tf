# ── Azure Data Factory ────────────────────────────────────────
resource "azurerm_data_factory" "velibdata" {
  name                = var.adf_name
  location            = var.location
  resource_group_name = var.resource_group_name

  # System-assigned managed identity — no credentials needed in code
  identity {
    type = "SystemAssigned"
  }
}

# ── RBAC: ADF managed identity → ADLS Gen2 ───────────────────
resource "azurerm_role_assignment" "adf_storage_contributor" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.velibdata.identity[0].principal_id
}

# ── RBAC: ADF managed identity → Event Hubs (receiver) ───────
resource "azurerm_role_assignment" "adf_eventhub_receiver" {
  scope                = var.eventhub_namespace_id
  role_definition_name = "Azure Event Hubs Data Receiver"
  principal_id         = azurerm_data_factory.velibdata.identity[0].principal_id
}

# ── Key Vault access: ADF managed identity reads secrets ──────
resource "azurerm_key_vault_access_policy" "adf" {
  key_vault_id = var.key_vault_id
  tenant_id    = var.tenant_id
  object_id    = azurerm_data_factory.velibdata.identity[0].principal_id

  secret_permissions = ["Get", "List"]
}

# ── Linked service: ADLS Gen2 ─────────────────────────────────
resource "azurerm_data_factory_linked_service_data_lake_storage_gen2" "adls" {
  name                = "ls_adls_velibdata"
  data_factory_id     = azurerm_data_factory.velibdata.id
  use_managed_identity = true
  url                 = "https://${var.storage_account_name}.dfs.core.windows.net"
}

# ── Linked service: Azure Event Hubs ─────────────────────────
resource "azurerm_data_factory_linked_service_azure_blob_storage" "eventhub_capture" {
  name            = "ls_eventhub_velibdata"
  data_factory_id = azurerm_data_factory.velibdata.id

  # ADF reads Event Hubs Capture output from ADLS (Avro files)
  # Connection string pulled from Key Vault at runtime
  connection_string = "@Microsoft.KeyVault(VaultName=${var.key_vault_name};SecretName=eventhub-listen-connection-string)"
}
