"""Configuration centralisee du projet VelibData.

Usage:
    from src.utils.config import api_settings
    print(api_settings.velib_station_status_url)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    velib_station_status_url: str = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
    velib_station_info_url: str = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"
    openmeteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    log_level: str = "INFO"


api_settings = APISettings()
