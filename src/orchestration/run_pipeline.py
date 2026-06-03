"""Local orchestration for the VelibData ingestion pipeline.

This module chains the validated local steps:

1. Normalize Event Hubs Capture Avro files into JSON.
2. Load normalized JSON envelopes into Azure SQL Bronze tables.
3. Run dbt models.
4. Run dbt tests.

It is intended as a lightweight local orchestrator before the same sequence is
implemented in Azure Data Factory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.transformations.load_bronze import (
    _get_sql_connection,
    ensure_bronze_schema,
    load_station_info,
    load_station_status,
    load_weather,
)
from src.transformations.normalize_eventhub_capture import normalize_avro_file
from src.utils.logger import get_logger

logger = get_logger(__name__)

Loader = Callable[[Any, dict[str, Any]], int]

SOURCE_LOADERS: dict[str, Loader] = {
    "velib_station_status": load_station_status,
    "velib_station_info": load_station_info,
    "open_meteo": load_weather,
}


def normalize_avro_directory(avro_dir: Path, normalized_dir: Path) -> list[Path]:
    """Normalize all Avro files found in a directory.

    Args:
        avro_dir: Directory containing Event Hubs Capture Avro files.
        normalized_dir: Directory where normalized JSON files will be written.

    Returns:
        Paths to the normalized JSON files.

    Raises:
        FileNotFoundError: If ``avro_dir`` does not exist.
        RuntimeError: If no Avro files are found.
    """
    if not avro_dir.is_dir():
        raise FileNotFoundError(f"Avro directory not found: {avro_dir}")

    avro_files = sorted(avro_dir.rglob("*.avro"))
    if not avro_files:
        raise RuntimeError(f"No Avro files found in: {avro_dir}")

    logger.info("pipeline_normalize_start", avro_dir=str(avro_dir), avro_file_count=len(avro_files))
    normalized_files = [normalize_avro_file(str(path), str(normalized_dir)) for path in avro_files]
    logger.info(
        "pipeline_normalize_complete",
        normalized_dir=str(normalized_dir),
        normalized_file_count=len(normalized_files),
    )
    return normalized_files


def _load_json(path: Path) -> dict[str, Any]:
    """Read a JSON file as an object."""
    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Normalized JSON must be an object: {path}")
    return data


def _extract_envelopes(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract normalized envelopes from either supported JSON shape.

    ``normalize_eventhub_capture.py`` writes a file-level object with a
    ``records`` array. This helper also accepts a single envelope directly,
    which keeps the orchestrator useful with manually prepared normalized files.
    """
    records = data.get("records")
    if records is None:
        return [data]

    if not isinstance(records, list):
        raise ValueError("The normalized JSON field 'records' must be a list")

    envelopes: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} in normalized JSON is not an object")
        envelopes.append(record)
    return envelopes


def _infer_source(envelope: dict[str, Any]) -> str | None:
    """Infer a source for legacy envelopes that do not contain ``source``."""
    source = envelope.get("source")
    if isinstance(source, str) and source:
        return source

    payload = envelope.get("payload", envelope)
    if not isinstance(payload, dict):
        return None

    if payload.get("data", {}).get("hourly"):
        return "open_meteo"

    stations = payload.get("stations", [])
    if not stations:
        return None

    first_station = stations[0]
    if not isinstance(first_station, dict):
        return None

    if "num_bikes_available" in first_station:
        return "velib_station_status"
    if {"name", "capacity", "lat", "lon"}.issubset(first_station):
        return "velib_station_info"

    return None


def _envelope_sort_key(envelope: dict[str, Any]) -> str:
    """Return a stable timestamp-like key used to select the latest snapshot."""
    return str(envelope.get("published_at") or envelope.get("fetched_at") or "")


def collect_latest_envelopes(normalized_files: list[Path]) -> dict[str, dict[str, Any]]:
    """Collect the latest normalized envelope for each supported source.

    The current Bronze loaders use ``TRUNCATE + INSERT`` and therefore model a
    snapshot. Loading only the latest envelope per source avoids repeatedly
    truncating the same Bronze table when several captured files are present.
    """
    latest_by_source: dict[str, dict[str, Any]] = {}

    for path in normalized_files:
        data = _load_json(path)
        for envelope in _extract_envelopes(data):
            source = _infer_source(envelope)
            if source not in SOURCE_LOADERS:
                raise ValueError(f"Unsupported or missing source in {path}: {source}")

            current = latest_by_source.get(source)
            if current is None or _envelope_sort_key(envelope) >= _envelope_sort_key(current):
                latest_by_source[source] = envelope

    logger.info("pipeline_envelopes_collected", source_count=len(latest_by_source), sources=sorted(latest_by_source))
    return latest_by_source


def load_bronze_from_normalized(normalized_files: list[Path]) -> None:
    """Load normalized JSON envelopes into Azure SQL Bronze tables.

    Args:
        normalized_files: Paths to normalized JSON files.

    Raises:
        ValueError: If a normalized envelope has an unsupported source.
        pyodbc.Error: If SQL connection or inserts fail.
    """
    latest_by_source = collect_latest_envelopes(normalized_files)
    logger.info("pipeline_bronze_load_start", source_count=len(latest_by_source))

    conn = _get_sql_connection()
    try:
        ensure_bronze_schema(conn)

        for source, envelope in latest_by_source.items():
            loader = SOURCE_LOADERS[source]
            row_count = loader(conn, envelope)
            logger.info(
                "pipeline_bronze_source_loaded",
                source=source,
                batch_id=envelope.get("batch_id"),
                row_count=row_count,
            )
    finally:
        conn.close()

    logger.info("pipeline_bronze_load_complete")


def run_command(command: list[str], cwd: Path) -> None:
    """Run a subprocess command and raise if it fails.

    Args:
        command: Command and arguments to execute.
        cwd: Working directory for the command.

    Raises:
        subprocess.CalledProcessError: If the command exits with a non-zero
            status code.
    """
    logger.info("pipeline_command_start", command=" ".join(command), cwd=str(cwd))
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        logger.error("pipeline_command_failed", command=" ".join(command), cwd=str(cwd), exit_code=result.returncode)
        raise subprocess.CalledProcessError(result.returncode, command)
    logger.info("pipeline_command_complete", command=" ".join(command), cwd=str(cwd))


def run_dbt(dbt_dir: Path) -> None:
    """Run dbt transformations and tests."""
    if not dbt_dir.is_dir():
        raise FileNotFoundError(f"dbt directory not found: {dbt_dir}")

    run_command(["uv", "run", "dbt", "run"], dbt_dir)
    run_command(["uv", "run", "dbt", "test"], dbt_dir)


def run_pipeline(avro_dir: Path, normalized_dir: Path, dbt_dir: Path) -> None:
    """Run the complete local pipeline."""
    logger.info(
        "pipeline_start",
        avro_dir=str(avro_dir),
        normalized_dir=str(normalized_dir),
        dbt_dir=str(dbt_dir),
    )
    normalized_files = normalize_avro_directory(avro_dir, normalized_dir)
    load_bronze_from_normalized(normalized_files)
    run_dbt(dbt_dir)
    logger.info("pipeline_complete")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the local VelibData pipeline.")
    parser.add_argument("--avro-dir", required=True, type=Path, help="Directory containing Event Hubs Capture Avro files.")
    parser.add_argument("--normalized-dir", required=True, type=Path, help="Output directory for normalized JSON files.")
    parser.add_argument("--dbt-dir", required=True, type=Path, help="dbt project directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint.

    Returns:
        ``0`` when all pipeline steps succeed, otherwise ``1``.
    """
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_pipeline(args.avro_dir, args.normalized_dir, args.dbt_dir)
    except Exception as exc:
        logger.error("pipeline_failed", error=str(exc))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
