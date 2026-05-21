"""Point d entree du pipeline d ingestion VelibData.

Fetch les APIs en parallele et ecrit les donnees brutes dans le Bronze layer.
Pour le dev, ecrit en local dans data/bronze/. Sera remplace par ADLS Gen2.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from src.ingestion.velib_client import fetch_station_info, fetch_station_status, fetch_weather
from src.utils.logger import get_logger

logger = get_logger(__name__)

LOCAL_BRONZE = Path("data/bronze")


def _write_bronze(data: dict, source: str) -> Path:
    """Ecrit les donnees brutes en JSON dans le bronze layer local."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    date_partition = datetime.now(UTC).strftime("%Y/%m/%d")

    output_dir = LOCAL_BRONZE / source / date_partition
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"{source}_{timestamp}.json"
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("bronze_written", path=str(filepath), size_kb=round(filepath.stat().st_size / 1024, 1))
    return filepath


async def run_ingestion() -> None:
    """Execute un cycle d ingestion complet."""
    logger.info("ingestion_cycle_start")

    status, info, weather = await asyncio.gather(
        fetch_station_status(),
        fetch_station_info(),
        fetch_weather(),
    )

    _write_bronze(status, "station_status")
    _write_bronze(info, "station_info")
    _write_bronze(weather, "weather")

    logger.info("ingestion_cycle_complete", stations=status["station_count"])


def main() -> None:
    asyncio.run(run_ingestion())


if __name__ == "__main__":
    main()
