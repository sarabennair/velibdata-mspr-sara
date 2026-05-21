"""Sends ingested data to Azure Event Hubs.

Retrieves the Event Hubs connection string from Azure Key Vault at runtime —
no credentials stored in code or environment files (CdC §8.5 — HIGH Critique).
"""

import json
import os

from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from src.utils.logger import get_logger

logger = get_logger(__name__)

_KEY_VAULT_URI = os.getenv("AZURE_KEY_VAULT_URI", "https://kv-velib-1c53.vault.azure.net/")

# Hub names matching Terraform eventhubs module
HUB_AVAILABILITY = "velib-availability"
HUB_STATION_INFO = "velib-station-info"
HUB_WEATHER = "velib-weather"


def _get_credential():
    """Returns Azure credential.

    Uses ClientSecretCredential when env vars are set (CI/CD, local dev with .env).
    Falls back to DefaultAzureCredential for managed identity environments (Azure VMs, ADF).
    """
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
    """Fetches Event Hubs send connection string from Key Vault."""
    credential = _get_credential()
    kv_client = SecretClient(vault_url=_KEY_VAULT_URI, credential=credential)
    secret = kv_client.get_secret("eventhub-send-connection-string")
    return secret.value


def send_to_eventhub(data: dict, hub_name: str) -> None:
    """Sends a single JSON payload to the specified Event Hub."""
    conn_str = _get_eventhub_connection_string()

    with EventHubProducerClient.from_connection_string(conn_str, eventhub_name=hub_name) as producer:
        batch = producer.create_batch()
        batch.add(EventData(json.dumps(data, ensure_ascii=False)))
        producer.send_batch(batch)

    logger.info("eventhub_sent", hub=hub_name, size_kb=round(len(json.dumps(data)) / 1024, 1))
