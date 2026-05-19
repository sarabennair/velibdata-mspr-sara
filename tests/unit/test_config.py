"""Tests unitaires pour la configuration."""


from src.utils.config import api_settings


def test_api_urls_configured():
    assert "station_status" in api_settings.velib_station_status_url
    assert "station_information" in api_settings.velib_station_info_url
    assert "open-meteo" in api_settings.openmeteo_base_url


def test_api_urls_are_https():
    assert api_settings.velib_station_status_url.startswith("https://")
    assert api_settings.velib_station_info_url.startswith("https://")
    assert api_settings.openmeteo_base_url.startswith("https://")
