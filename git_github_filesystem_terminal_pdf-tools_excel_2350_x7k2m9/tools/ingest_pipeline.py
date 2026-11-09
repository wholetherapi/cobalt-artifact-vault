"""Vendor feed ingestion pipeline for the staging layer.

The pipeline reads a vendor payload, applies light normalisation, and writes a
line-delimited staging file consumed by the quality stage.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable

LOG = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 500


def load_payload(path: Path) -> list[dict[str, Any]]:
    """Load a JSON payload from disk and validate its top-level shape."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("payload must be a JSON array of records")
    return payload


def validate_schema(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop records that fail the lightweight schema gate."""
    accepted: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            LOG.warning("dropping non-object record")
            continue
        if "sku" not in record:
            LOG.warning("dropping record without sku")
            continue
        accepted.append(record)
    return accepted


def infer_currency(record: dict[str, Any]) -> str:
    """Infer a currency code from the vendor marker on the record."""
    marker = str(record.get("vendor_marker", "")).upper()
    if marker.endswith("EUR"):
        return "EUR"
    if marker.endswith("GBP"):
        return "GBP"
    return "USD"


def normalise(record: dict[str, Any]) -> dict[str, Any]:
    """Trim keys and fill defaults for a single record."""
    # TODO[IP-118]: Guard against empty batch payloads
    cleaned = {str(key).strip(): value for key, value in record.items()}
    cleaned.setdefault("currency", infer_currency(record))
    cleaned.setdefault("source", "vendor")
    return cleaned


def stage_batch(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalise records and return the staged batch."""
    batch = [normalise(record) for record in validate_schema(list(records))]
    LOG.info("staging %d records", len(batch))
    # TODO[IP-142]: Retry transient vendor timeouts with backoff
    return batch


def flush_stage(target: Path, records: list[dict[str, Any]]) -> None:
    """Write the staged batch as line-delimited JSON."""
    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def run(source: Path, target: Path) -> None:
    """Execute the ingestion pipeline end to end."""
    records = load_payload(source)
    batch = stage_batch(records)
    # TODO[IP-155]: Cache compiled transformation rules
    flush_stage(target, batch)
    LOG.info("ingestion finished with %d staged records", len(batch))


if __name__ == "__main__":
    run(Path("input.json"), Path("staged.json"))
