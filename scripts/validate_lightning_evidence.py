#!/usr/bin/env python3
"""Validate local lightning CSV evidence and print an aggregate-only summary."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from meteo_audit.lightning_qc import inspect_lightning_evidence  # noqa: E402


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-csv", required=True, type=Path)
    parser.add_argument("--examples-csv", required=True, type=Path)
    parser.add_argument("--target-source", required=True,
                        help="source label in the supplied summary CSV; it is not emitted")
    args = parser.parse_args()
    result = inspect_lightning_evidence(
        read_csv(args.summary_csv), read_csv(args.examples_csv),
        target_source=args.target_source,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
