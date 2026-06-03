"""Configuration centralisee du projet VelibData.

Usage:
    from src.utils.config import api_settings, azure_settings, eventhub_settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    velib_station_status_url: str = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
    velib_station_info_url: str = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"
    openmeteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    log_level: str = "INFO"


class AzureSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    adls_account_name: str = ""
    adls_account_key: str = ""
    adls_container_bronze: str = "bronze"
    adls_container_silver: str = "silver"
    adls_container_gold: str = "gold"


class EventHubSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ingestion_mode: str = "eventhub"
    local_output_dir: str = "data/local_bronze"
    azure_key_vault_uri: str = "https://kv-velib-1c53.vault.azure.net/"
    eventhub_connection_string: str = ""
    eventhub_send_connection_secret_name: str = "eventhub-send-connection-string"
    eventhub_availability_name: str = "velib-availability"
    eventhub_station_info_name: str = "velib-station-info"
    eventhub_weather_name: str = "velib-weather"
    eventhub_schema_version: str = "1.0"


api_settings = APISettings()
azure_settings = AzureSettings()
eventhub_settings = EventHubSettings()
