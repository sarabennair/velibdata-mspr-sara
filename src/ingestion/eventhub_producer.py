"""Sends ingested data to Azure Event Hubs.

Retrieves the Event Hubs connection string from Azure Key Vault at runtime by
default. Local development can also provide EVENTHUB_CONNECTION_STRING.
"""

import json
import os
from typing import Any

from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from src.utils.config import eventhub_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Hub names matching Terraform eventhubs module
HUB_AVAILABILITY = eventhub_settings.eventhub_availability_name
HUB_STATION_INFO = eventhub_settings.eventhub_station_info_name
HUB_WEATHER = eventhub_settings.eventhub_weather_name


def _get_credential():
    """Returns Azure credential for Key Vault access."""
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

    if tenant_id and client_id and client_secret:
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
    return DefaultAzureCredential()


def _get_eventhub_connection_string() -> str:
    """Fetches the Event Hubs send connection string."""
    if eventhub_settings.eventhub_connection_string:
        return eventhub_settings.eventhub_connection_string

    credential = _get_credential()
    kv_client = SecretClient(vault_url=eventhub_settings.azure_key_vault_uri, credential=credential)
    secret = kv_client.get_secret(eventhub_settings.eventhub_send_connection_secret_name)
    return secret.value


def send_to_eventhub(
    data: dict[str, Any],
    hub_name: str,
    *,
    event_type: str,
    partition_key: str | None = None,
) -> None:
    """Sends a single JSON payload to the specified Event Hub."""
    conn_str = _get_eventhub_connection_string()
    body = json.dumps(data, ensure_ascii=False)
    event = EventData(body)
    event.properties = {
        "event_type": event_type,
        "source": data.get("source", ""),
        "schema_version": data.get("schema_version", ""),
    }

    with EventHubProducerClient.from_connection_string(conn_str, eventhub_name=hub_name) as producer:
        batch = producer.create_batch(partition_key=partition_key)
        batch.add(event)
        producer.send_batch(batch)

    logger.info(
        "eventhub_sent",
        hub=hub_name,
        event_type=event_type,
        partition_key=partition_key,
        size_kb=round(len(body.encode("utf-8")) / 1024, 1),
    )


def send_source_payloads(
    *,
    station_status: dict[str, Any],
    station_info: dict[str, Any],
    weather: dict[str, Any],
) -> None:
    """Sends the three source payloads to their dedicated Event Hubs."""
    send_to_eventhub(
        station_status,
        HUB_AVAILABILITY,
        event_type="velib.station_status.snapshot",
        partition_key="station_status",
    )
    send_to_eventhub(
        station_info,
        HUB_STATION_INFO,
        event_type="velib.station_info.snapshot",
        partition_key="station_info",
    )
    send_to_eventhub(
        weather,
        HUB_WEATHER,
        event_type="open_meteo.weather.snapshot",
        partition_key="weather",
    )
