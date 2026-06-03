"""Point d entree du pipeline d ingestion VelibData.

Fetch les APIs en parallele et publie les donnees brutes dans Azure Event Hubs.
Event Hubs Capture se charge ensuite de deposer les evenements dans ADLS Bronze.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.ingestion.eventhub_producer import send_source_payloads
from src.ingestion.velib_client import fetch_station_info, fetch_station_status, fetch_weather
from src.utils.config import eventhub_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _build_event(source: str, payload: dict, batch_id: str) -> dict:
    """Wraps a source payload with ingestion metadata before publication."""
    published_at = datetime.now(UTC).isoformat()
    return {
        "schema_version": eventhub_settings.eventhub_schema_version,
        "batch_id": batch_id,
        "source": source,
        "fetched_at": payload.get("fetched_at"),
        "published_at": published_at,
        "payload": payload,
    }


def _write_local_snapshot(data: dict, source: str) -> str:
    """Writes local JSON snapshots for development without Azure credentials."""
    now = datetime.now(UTC)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    directory = Path(eventhub_settings.local_output_dir) / source
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{source}_{timestamp}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("local_snapshot_written", source=source, path=str(path))
    return str(path)


async def run_ingestion() -> None:
    """Execute un cycle d ingestion complet vers Event Hubs ou local."""
    mode = eventhub_settings.ingestion_mode.lower()
    batch_id = str(uuid4())
    logger.info("ingestion_cycle_start", target=mode, batch_id=batch_id)

    try:
        status, info, weather = await asyncio.gather(
            fetch_station_status(),
            fetch_station_info(),
            fetch_weather(),
        )

        status_event = _build_event("velib_station_status", status, batch_id)
        info_event = _build_event("velib_station_info", info, batch_id)
        weather_event = _build_event("open_meteo", weather, batch_id)

        if mode == "eventhub":
            send_source_payloads(
                station_status=status_event,
                station_info=info_event,
                weather=weather_event,
            )
        elif mode == "local":
            _write_local_snapshot(status_event, "station_status")
            _write_local_snapshot(info_event, "station_info")
            _write_local_snapshot(weather_event, "weather")
        else:
            raise ValueError(f"Mode d ingestion non supporte: {mode}")

        logger.info(
            "ingestion_cycle_complete",
            batch_id=batch_id,
            target=mode,
            station_status_count=status["station_count"],
            station_info_count=info["station_count"],
        )
    except Exception as exc:
        logger.error("ingestion_cycle_failed", batch_id=batch_id, target=mode, error=str(exc))
        raise


def main() -> None:
    asyncio.run(run_ingestion())


if __name__ == "__main__":
    main()
