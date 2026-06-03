"""Normalize Azure Event Hubs Capture Avro files into JSON.

Event Hubs Capture writes Avro records whose ``Body`` field contains the event
payload as bytes. In this project, the body is a JSON document produced by the
ingestion layer with the following envelope:

    {
      "schema_version": "1.0",
      "batch_id": "...",
      "source": "velib_station_status",
      "fetched_at": "...",
      "published_at": "...",
      "payload": {...}
    }

This module decodes every Avro record, extracts the envelope metadata and
payload, then writes a normalized JSON file that can be used by the downstream
Bronze loading step.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastavro import reader

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventHubCaptureNormalizationError(ValueError):
    """Raised when an Event Hubs Capture Avro record cannot be normalized."""


def _decode_body(record: dict[str, Any], record_index: int) -> dict[str, Any]:
    """Decode and parse the JSON body from one Event Hubs Capture Avro record.

    Args:
        record: Raw Avro record returned by ``fastavro.reader``.
        record_index: Zero-based record index, used for actionable error
            messages and logs.

    Returns:
        Parsed JSON envelope as a dictionary.

    Raises:
        EventHubCaptureNormalizationError: If the ``Body`` field is missing,
            not bytes-like, not valid UTF-8, or not valid JSON.
    """
    body = record.get("Body")
    if body is None:
        raise EventHubCaptureNormalizationError(f"Record {record_index} is missing Body")

    if not isinstance(body, bytes | bytearray):
        raise EventHubCaptureNormalizationError(
            f"Record {record_index} Body must be bytes, got {type(body).__name__}"
        )

    try:
        decoded = bytes(body).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EventHubCaptureNormalizationError(f"Record {record_index} Body is not valid UTF-8") from exc

    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise EventHubCaptureNormalizationError(f"Record {record_index} Body is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise EventHubCaptureNormalizationError(f"Record {record_index} Body JSON must be an object")

    return parsed


def _normalize_envelope(envelope: dict[str, Any], record_index: int) -> dict[str, Any]:
    """Extract metadata and payload from one parsed ingestion envelope.

    Args:
        envelope: Parsed JSON document from the Event Hubs message body.
        record_index: Zero-based record index, used for error messages.

    Returns:
        Normalized dictionary containing the metadata fields and ``payload``.

    Raises:
        EventHubCaptureNormalizationError: If ``payload`` is absent.
    """
    if "payload" not in envelope:
        raise EventHubCaptureNormalizationError(f"Record {record_index} is missing payload")

    return {
        "schema_version": envelope.get("schema_version"),
        "batch_id": envelope.get("batch_id"),
        "source": envelope.get("source"),
        "fetched_at": envelope.get("fetched_at"),
        "published_at": envelope.get("published_at"),
        "payload": envelope["payload"],
    }


def _build_output_path(input_path: Path, output_dir: Path) -> Path:
    """Build a deterministic normalized JSON output path for an Avro file.

    Args:
        input_path: Source Avro file path.
        output_dir: Directory where the normalized JSON file should be written.

    Returns:
        Output path using the Avro filename stem and a ``.json`` suffix.
    """
    return output_dir / f"{input_path.stem}.json"


def normalize_avro_file(input_path: str, output_dir: str) -> Path:
    """Normalize one Event Hubs Capture Avro file into a JSON file.

    The output JSON has file-level metadata and a ``records`` array. Each record
    contains the ingestion metadata from the Event Hubs body plus the original
    source payload.

    Args:
        input_path: Path to the Event Hubs Capture Avro file.
        output_dir: Directory where the normalized JSON file will be created.

    Returns:
        Path to the normalized JSON file.

    Raises:
        FileNotFoundError: If ``input_path`` does not exist.
        EventHubCaptureNormalizationError: If a record is malformed.
        OSError: If the input cannot be read or the output cannot be written.
    """
    avro_path = Path(input_path)
    normalized_dir = Path(output_dir)

    if not avro_path.is_file():
        raise FileNotFoundError(f"Avro input file not found: {avro_path}")

    normalized_dir.mkdir(parents=True, exist_ok=True)
    output_path = _build_output_path(avro_path, normalized_dir)

    records: list[dict[str, Any]] = []
    logger.info("eventhub_capture_normalization_start", input_path=str(avro_path), output_dir=str(normalized_dir))

    with avro_path.open("rb") as avro_file:
        for index, record in enumerate(reader(avro_file)):
            envelope = _decode_body(record, index)
            records.append(_normalize_envelope(envelope, index))

    output = {
        "normalized_at": datetime.now(UTC).isoformat(),
        "input_file": str(avro_path),
        "record_count": len(records),
        "records": records,
    }
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(
        "eventhub_capture_normalization_complete",
        input_path=str(avro_path),
        output_path=str(output_path),
        record_count=len(records),
    )
    return output_path


def _main(argv: list[str]) -> int:
    """Run the command-line interface.

    Args:
        argv: CLI arguments excluding the Python executable and module name.

    Returns:
        Process exit code. ``0`` means success, ``1`` means invalid usage or a
        normalization failure.
    """
    if len(argv) != 2:
        print(
            "Usage: python -m src.transformations.normalize_eventhub_capture <input.avro> <output_dir>",
            file=sys.stderr,
        )
        return 1

    input_path, output_dir = argv
    try:
        output_path = normalize_avro_file(input_path, output_dir)
    except Exception as exc:
        logger.error("eventhub_capture_normalization_failed", input_path=input_path, output_dir=output_dir, error=str(exc))
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
