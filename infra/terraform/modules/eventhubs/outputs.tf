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
