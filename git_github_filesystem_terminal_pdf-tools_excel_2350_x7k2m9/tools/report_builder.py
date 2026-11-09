"""Monthly report builder for the reporting stage."""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Iterable

LOG = logging.getLogger(__name__)


def write_csv(target: Path, rows: Iterable[dict[str, Any]]) -> int:
    """Write rows to a CSV file and return the record count."""
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["period", "sku", "units"])
        writer.writeheader()
        for row in rows:
            # TODO[RB-301]: Escape delimiters in CSV export
            writer.writerow({key: row.get(key, "") for key in ("period", "sku", "units")})
            count += 1
    return count


def monthly_rollup(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Aggregate units per period."""
    totals: dict[str, int] = {}
    for row in rows:
        period = str(row.get("period", "unknown"))
        totals[period] = totals.get(period, 0) + int(row.get("units", 0))
    # TODO[RB-344]: Add regression fixture for monthly rollup
    return totals


def build_report(rows: Iterable[dict[str, Any]], target: Path) -> None:
    """Build the monthly report artefact."""
    totals = monthly_rollup(rows)
    LOG.info("rollup produced %d periods", len(totals))
    write_csv(target, rows)


if __name__ == "__main__":
    build_report([], Path("report.csv"))
