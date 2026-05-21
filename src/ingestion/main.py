"""Point d'entrée du pipeline d'ingestion VelibData.

Fetch les APIs en parallèle et envoie les données brutes vers Azure Event Hubs.
ADF récupère les messages depuis Event Hubs et les écrit dans ADLS Gen2 Bronze.

En dev local (sans Azure), définir USE_LOCAL_STORAGE=true pour écrire dans data/bronze/.
"""

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from src.ingestion.eventhub_producer import (
    HUB_AVAILABILITY,
    HUB_STATION_INFO,
    HUB_WEATHER,
    send_to_eventhub,
)
from src.ingestion.velib_client import fetch_station_info, fetch_station_status, fetch_weather
from src.utils.logger import get_logger

logger = get_logger(__name__)

LOCAL_BRONZE = Path("data/bronze")
USE_LOCAL = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"


def _write_local(data: dict, source: str) -> Path:
    """Writes raw JSON locally — only used when USE_LOCAL_STORAGE=true (dev/offline)."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    date_partition = datetime.now(UTC).strftime("%Y/%m/%d")

    output_dir = LOCAL_BRONZE / source / date_partition
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{source}_{timestamp}.json"
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("local_bronze_written", path=str(filepath), size_kb=round(filepath.stat().st_size / 1024, 1))
    return filepath


def _write_bronze(data: dict, source: str, hub_name: str) -> None:
    """Routes data to Event Hubs (cloud) or local file (dev)."""
    if USE_LOCAL:
        _write_local(data, source)
    else:
        send_to_eventhub(data, hub_name)


async def run_ingestion() -> None:
    """Executes one full ingestion cycle."""
    logger.info("ingestion_cycle_start", destination="eventhubs" if not USE_LOCAL else "local")

    status, info, weather = await asyncio.gather(
        fetch_station_status(),
        fetch_station_info(),
        fetch_weather(),
    )

    _write_bronze(status, "station_status", HUB_AVAILABILITY)
    _write_bronze(info, "station_info", HUB_STATION_INFO)
    _write_bronze(weather, "weather", HUB_WEATHER)

    logger.info("ingestion_cycle_complete", stations=status["station_count"])


def main() -> None:
    asyncio.run(run_ingestion())


if __name__ == "__main__":
    main()
