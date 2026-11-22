#!/usr/bin/env python3
"""Compute conditional 5-minute slot arithmetic for already identified long gaps.

This is not an expected-slot or missing-measurement determination: operation,
valid cadence epochs, and downtime are not established by endpoint timestamps.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/2026-11-12-long-gap-cases-ge-1d.csv"
OUT = ROOT / "reports/2026-11-12-long-gap-conditional-5m-slots.csv"
REPORT = ROOT / "reports/2026-11-12-long-gap-conditional-5m-slots.md"
STEP = 300
with SOURCE.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 44
out = []
for r in rows:
    delta = int(r["delta_seconds"])
    aligned = delta % STEP == 0
    candidate = delta // STEP - 1 if aligned else ""
    out.append({
        "utc_year": r["utc_year"], "utc_month": r["utc_month"],
        "prev_utc": r["prev_utc"], "target_utc": r["target_utc"],
        "delta_seconds": delta, "prev_interval_min": r["prev_interval"],
        "current_interval_min": r["current_interval"],
        "delta_mod_300_seconds": delta % STEP,
        "aligned_to_300s_endpoint_difference": str(aligned).lower(),
        "conditional_intermediate_5m_slots_if_continuous": candidate,
        "review_flags": r["review_flags"],
    })
out.sort(key=lambda x: (x["prev_utc"], x["target_utc"]))
fields = list(out[0])
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(out)
aligned_count = sum(x["aligned_to_300s_endpoint_difference"] == "true" for x in out)
total = sum(int(x["conditional_intermediate_5m_slots_if_continuous"]) for x in out)
maxrow = max(out, key=lambda x: int(x["conditional_intermediate_5m_slots_if_continuous"]))
assert aligned_count == 44
assert total == 97_048
REPORT.write_text(f"""# Podmíněná pětiminutová slotová aritmetika dlouhých mezer

Deterministický výpočet z již ověřeného katalogu 44 sousedních delt ≥24 h. Všech 44 rozdílů krajních timestampů je násobkem 300 s; při čistě hypotetické nepřerušené pětiminutové kadenci by mezi krajními záznamy připadalo celkem **{total:,} mezilehlých slotů**. Největší podmíněný počet je {int(maxrow['conditional_intermediate_5m_slots_if_continuous']):,} v okně {maxrow['prev_utc']} → {maxrow['target_utc']}.

Tento součet **není počet očekávaných ani chybějících měření**. Předpokládá nepřerušený pětiminutový provoz po celé mezery. Není doloženo, zda stanice běžela, zda existovaly stejné provozní epochy, zda šlo o odstávku, ztrátu exportu či chybu archivace, ani zda endpointy odpovídají stabilní timestampové sémantice. Výsledek proto slouží pouze k prioritizaci rozsahu pro ER-01/ER-02; modelová rekonstrukce z něj nevyplývá. Případy z Q1 2018 zůstávají průběžné a rok 2021 diagnostický.

Vstup: `reports/2026-11-12-long-gap-cases-ge-1d.csv`. Reprodukce: `scripts/derive_long_gap_conditional_slots.py`. Řádkové výsledky: `reports/2026-11-12-long-gap-conditional-5m-slots.csv`.
""", encoding="utf-8")
print(f"gaps={len(out)} aligned={aligned_count} conditional_slots={total}")
print(f"largest={maxrow['prev_utc']}->{maxrow['target_utc']} slots={maxrow['conditional_intermediate_5m_slots_if_continuous']}")
