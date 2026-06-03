# ── Event Hubs Namespace ──────────────────────────────────────
resource "azurerm_eventhub_namespace" "velibdata" {
  name                = var.eventhub_namespace_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Standard"
  capacity            = 1
}

# ── 3 Event Hubs (one per data source) ───────────────────────
resource "azurerm_eventhub" "availability" {
  name                = "velib-availability"
  namespace_name      = azurerm_eventhub_namespace.velibdata.name
  resource_group_name = var.resource_group_name
  partition_count     = 2
  message_retention   = 1

  capture_description {
    enabled             = true
    encoding            = "Avro"
    interval_in_seconds = var.capture_interval_in_seconds
    size_limit_in_bytes = var.capture_size_limit_in_bytes
    skip_empty_archives = true

    destination {
      name                = "EventHubArchive.AzureBlockBlob"
      archive_name_format = "eventhubs/velib-availability/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
      blob_container_name = var.capture_container_name
      storage_account_id  = var.capture_storage_account_id
    }
  }
}

resource "azurerm_eventhub" "station_info" {
  name                = "velib-station-info"
  namespace_name      = azurerm_eventhub_namespace.velibdata.name
  resource_group_name = var.resource_group_name
  partition_count     = 2
  message_retention   = 1

  capture_description {
    enabled             = true
    encoding            = "Avro"
    interval_in_seconds = var.capture_interval_in_seconds
    size_limit_in_bytes = var.capture_size_limit_in_bytes
    skip_empty_archives = true

    destination {
      name                = "EventHubArchive.AzureBlockBlob"
      archive_name_format = "eventhubs/velib-station-info/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
      blob_container_name = var.capture_container_name
      storage_account_id  = var.capture_storage_account_id
    }
  }
}

resource "azurerm_eventhub" "weather" {
  name                = "velib-weather"
  namespace_name      = azurerm_eventhub_namespace.velibdata.name
  resource_group_name = var.resource_group_name
  partition_count     = 2
  message_retention   = 1

  capture_description {
    enabled             = true
    encoding            = "Avro"
    interval_in_seconds = var.capture_interval_in_seconds
    size_limit_in_bytes = var.capture_size_limit_in_bytes
    skip_empty_archives = true

    destination {
      name                = "EventHubArchive.AzureBlockBlob"
      archive_name_format = "eventhubs/velib-weather/{Namespace}/{EventHub}/{PartitionId}/{Year}/{Month}/{Day}/{Hour}/{Minute}/{Second}"
      blob_container_name = var.capture_container_name
      storage_account_id  = var.capture_storage_account_id
    }
  }
}

# ── Authorization rule: pipeline can SEND events ─────────────
resource "azurerm_eventhub_namespace_authorization_rule" "pipeline_send" {
  name                = "pipeline-send"
  namespace_name      = azurerm_eventhub_namespace.velibdata.name
  resource_group_name = var.resource_group_name
  listen              = false
  send                = true
  manage              = false
}

# ── Authorization rule: ADF can LISTEN to events ─────────────
resource "azurerm_eventhub_namespace_authorization_rule" "adf_listen" {
  name                = "adf-listen"
  namespace_name      = azurerm_eventhub_namespace.velibdata.name
  resource_group_name = var.resource_group_name
  listen              = true
  send                = false
  manage              = false
}

# ── Store connection strings in Key Vault ────────────────────
resource "azurerm_key_vault_secret" "eventhub_send_connection_string" {
  name         = "eventhub-send-connection-string"
  value        = azurerm_eventhub_namespace_authorization_rule.pipeline_send.primary_connection_string
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "eventhub_listen_connection_string" {
  name         = "eventhub-listen-connection-string"
  value        = azurerm_eventhub_namespace_authorization_rule.adf_listen.primary_connection_string
  key_vault_id = var.key_vault_id
}

resource "azurerm_key_vault_secret" "eventhub_namespace_name" {
  name         = "eventhub-namespace-name"
  value        = azurerm_eventhub_namespace.velibdata.name
  key_vault_id = var.key_vault_id
}
