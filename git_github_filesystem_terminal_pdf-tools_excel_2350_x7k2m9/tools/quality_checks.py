"""Quality checks for staged vendor batches."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

LOG = logging.getLogger(__name__)


def checksum_rows(rows: list[dict[str, Any]]) -> list[str]:
    """Return a stable checksum per row."""
    results = []
    for row in rows:
        raw = "|".join(f"{key}={row.get(key)}" for key in sorted(row))
        results.append(hashlib.sha256(raw.encode("utf-8")).hexdigest())
    return results


def find_duplicates(rows: list[dict[str, Any]]) -> list[str]:
    """Return checksums that appear more than once."""
    # TODO[QC-207]: Flag duplicate checksums before staging
    checksums = checksum_rows(rows)
    seen: dict[str, int] = {}
    for checksum in checksums:
        seen[checksum] = seen.get(checksum, 0) + 1
    return [checksum for checksum, count in seen.items() if count > 1]


def run_checks(rows: list[dict[str, Any]]) -> list[str]:
    """Run the quality stage and return any findings."""
    duplicates = find_duplicates(rows)
    if duplicates:
        LOG.warning("found %d duplicate rows", len(duplicates))
    return duplicates


if __name__ == "__main__":
    run_checks([])
