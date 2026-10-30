#!/usr/bin/env python3
"""Summarize official CHMI July 2021 SRA10M CSV files by Prague local day."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from meteo_audit.chmi_rainfall import summarize_chmi_10min
from meteo_audit.time_bounds import PRAGUE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_files", type=Path, nargs="+", help="CHMI SRA10M CSV files")
    args = parser.parse_args()

    start = int(datetime(2021, 7, 1, tzinfo=PRAGUE).timestamp())
    end = int(datetime(2021, 8, 1, tzinfo=PRAGUE).timestamp())
    rows = []
    for path in args.csv_files:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            rows.extend(csv.DictReader(stream))

    summary = summarize_chmi_10min(rows, start, end)
    output = []
    for (station, day), values in sorted(summary.items()):
        output.append(
            {
                "station": station,
                "local_day": day.isoformat(),
                "recorded_intervals": values["recorded_intervals"],
                "valid_intervals": values["valid_intervals"],
                "rejected_intervals": values["rejected_intervals"],
                "valid_mm": format(Decimal(values["valid_mm"]), "f"),
            }
        )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
