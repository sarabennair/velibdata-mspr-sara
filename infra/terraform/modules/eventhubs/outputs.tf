output "eventhub_namespace_id" {
  value = azurerm_eventhub_namespace.velibdata.id
}

output "eventhub_namespace_name" {
  value = azurerm_eventhub_namespace.velibdata.name
}

output "availability_hub_name" {
  value = azurerm_eventhub.availability.name
}

output "station_info_hub_name" {
  value = azurerm_eventhub.station_info.name
}

output "weather_hub_name" {
  value = azurerm_eventhub.weather.name
}

output "capture_container_name" {
  value = var.capture_container_name
}

output "capture_interval_in_seconds" {
  value = var.capture_interval_in_seconds
}

output "capture_size_limit_in_bytes" {
  value = var.capture_size_limit_in_bytes
}
