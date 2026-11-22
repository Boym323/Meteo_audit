#!/usr/bin/env python3
"""Validate high-level reconstruction history audit ledger arithmetic."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/RECONSTRUCTION_HISTORY_AUDIT.csv"
REPORT_PATH = ROOT / "reports/RECONSTRUCTION_HISTORY_AUDIT.md"


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    values = {(r['record_type'], r['variable'], r['state'], r['metric']): r['value'] for r in rows}
    assert values[('event_totals', 'all', 'applied', 'events')] == '94930'
    assert values[('event_totals', 'all', 'reverted', 'events')] == '17842'
    repeated = {'outHumidity':94,'outTemp':0,'rain':197,'rainRate':3146}
    assert sum(repeated.values()) == 94930 - 91493
    for var, n in repeated.items():
        ev=int(values[('event_totals',var,'applied','events')])
        pairs=int(values[('event_totals',var,'applied','unique_target_variable_pairs')])
        assert ev - pairs == n
    for var in ('outHumidity','outTemp','rainRate'):
        t=int(values[('latest_expected',var,'applied','targets')])
        m=int(values[('latest_expected',var,'applied','current_matches')])
        x=int(values[('latest_expected',var,'applied','current_mismatch')])
        assert t == m + x
    for state,targets,matches,mismatch in [('applied',879,733,146),('reverted',8681,7330,1351)]:
        assert int(values[('latest_expected','rain',state,'targets')]) == targets
        assert int(values[('latest_expected','rain',state,'current_matches')]) == matches
        assert int(values[('latest_expected','rain',state,'current_mismatch')]) == mismatch
        assert targets == matches + mismatch
    assert 146 + 1351 == 1497
    assert values[('rain_july_2021','all','latest_history_current_mismatch','targets')] == '1497'
    assert values[('rain_july_2021','all','current_matches_chmi_artifact','targets')] == '1497'
    report=REPORT_PATH.read_text(encoding='utf-8')
    for phrase in ('částečný audit', 'ER-23', 'ER-24', 'nepředstavuje kompletní audit'):
        assert phrase in report, phrase
    print(f"reconstruction history audit: OK ({len(rows)} ledger rows; 1,497 July 2021 artifact matches)")


if __name__ == '__main__':
    main()
