#!/usr/bin/env python3
"""Build and validate dynamic value provenance totals for a concordance snapshot."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from meteo_audit.provenance_counts import build_provenance_counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "data/historical_value_concordance.sqlite")
    parser.add_argument("--output", type=Path, default=ROOT / "PROVENANCE_COUNTS_CORRECTED.json")
    args = parser.parse_args()
    result = build_provenance_counts(args.database, args.output)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "snapshot_sha256": result["source_snapshot_sha256"],
        "snapshot_rows": result["snapshot_rows"],
        "field_count": result["field_count"],
        "field_value_total": result["field_value_total"],
        "nonempty_total": result["nonempty_total"],
        "missing_values": result["missing_values"],
        "known_snapshot_comparison": result.get("known_snapshot_comparison"),
        "invariants": result["invariants"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
