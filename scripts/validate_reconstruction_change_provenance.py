#!/usr/bin/env python3
"""Validate aggregate reconstruction_changes provenance coverage checkpoint."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/2026-11-13-reconstruction-change-provenance-coverage.csv"
REPORT_PATH = ROOT / "reports/2026-11-13-reconstruction-change-provenance-coverage.md"


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    def get(var: str, state: str, metric: str, record_type: str = "coverage") -> int:
        match = [r for r in rows if r["record_type"] == record_type and r["variable"] == var
                 and r["state"] == state and r["metric"] == metric]
        assert len(match) == 1, (var, state, metric, len(match))
        return int(match[0]["value"])

    expected = {
        ("outHumidity", "applied"): (20806,20712,20142,664,0),
        ("outTemp", "applied"): (10127,10127,9741,386,0),
        ("rain", "applied"): (1076,879,1055,21,0),
        ("rain", "reverted"): (8921,8921,8921,0,0),
        ("rainRate", "applied"): (62921,59775,62900,21,243),
        ("rainRate", "reverted"): (8921,8921,8921,0,0),
    }
    for (var,state),(events,pairs,exact,offset,source_null) in expected.items():
        assert get(var,state,"events") == events
        assert get(var,state,"target_variable_pairs") == pairs
        assert get(var,state,"source_time_equals_target") == exact
        assert get(var,state,"source_time_differs_target") == offset
        assert exact + offset == events
        assert get(var,state,"source_value_missing") == source_null
        for metric in ("source_database_missing","reason_missing","batch_key_missing","applied_at_missing"):
            assert get(var,state,metric) == 0
    assert sum(v[4] for v in expected.values()) == 243
    assert sum(v[3] for v in expected.values()) == 1092
    report = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in ("112 772 událostí", "1 092 eventů", "ER-25", "nebyly pro každý event znovu ověřeny"):
        assert phrase in report, phrase
    print(f"reconstruction change provenance: OK ({len(rows)} aggregate rows; 112,772 events)")


if __name__ == "__main__":
    main()
