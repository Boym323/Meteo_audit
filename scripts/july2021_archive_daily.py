#!/usr/bin/env python3
"""Read-only daily summary of an exported WeeWX archive CSV."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from meteo_audit.rain_reconstruction import summarize_archive
from meteo_audit.time_bounds import PRAGUE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="CSV with dateTime, interval, rain")
    args = parser.parse_args()

    start = int(datetime(2021, 7, 1, tzinfo=PRAGUE).timestamp())
    end = int(datetime(2021, 8, 1, tzinfo=PRAGUE).timestamp())
    with args.csv_file.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    daily = summarize_archive(rows, start, end)
    result = [
        {
            "local_day": day.isoformat(),
            "intervals": bucket["intervals"],
            "unknown_intervals": bucket["unknown_intervals"],
            "known_mm": format(Decimal(bucket["known_mm"]), "f"),
        }
        for day, bucket in sorted(daily.items())
    ]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
