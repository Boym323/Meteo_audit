#!/usr/bin/env python3
"""Create a deterministic triage extract of gaps >=24 h from the validated catalog."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "reports/2026-11-12-gap-event-catalog.csv"
out_csv = ROOT / "reports/2026-11-12-long-gap-cases-ge-1d.csv"
out_md = ROOT / "reports/2026-11-12-long-gap-triage.md"
with source.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
long = [r for r in rows if int(r["delta_seconds"]) >= 86_400]
fields = ["utc_year", "utc_month", "prev_utc", "target_utc", "delta_seconds",
          "prev_interval", "current_interval", "review_flags"]
for r in long:
    flags = ["ER-01: epoch/expected-slot classification unresolved", "ER-02: long-outage reconstruction expert review"]
    if r["utc_year"] == "2021":
        flags.append("2021 diagnostic only")
    if r["utc_year"] == "2018" and r["utc_month"] in {"1", "2", "3"}:
        flags.append("2018 Q1 interim/live")
    r["review_flags"] = "; ".join(flags)
with out_csv.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows({key: r[key] for key in fields} for r in sorted(long, key=lambda r: (int(r["prev_ts"]), int(r["target_ts"]))))
by_year = Counter(r["utc_year"] for r in long)
by_interval = Counter((r["prev_interval"], r["current_interval"]) for r in long)
long7 = sum(int(r["delta_seconds"]) >= 604_800 for r in long)
long90 = sum(int(r["delta_seconds"]) >= 7_776_000 for r in long)
assert len(rows) == 24_523
assert len(long) == 44 and long7 == 5 and long90 == 1
assert by_interval == Counter({("5", "5"): 44})
lines = [
    "# Triáž dlouhých časových mezer (>=24 h)", "",
    "Výstup je lokální deterministický výřez z validovaného event katalogu; nevytváří missing-slot count ani příčinu. Každý případ je označen pro ER-01/ER-02. Zdroj: `reports/2026-11-12-gap-event-catalog.csv`; reprodukce: `scripts/summarize_long_gap_cases.py`.", "",
    "## Souhrn", "",
    f"- {len(long)} kandidátních sousedních delt >=24 h; {long7} >=7 d; {long90} >=90 d.",
    "- Všech 44 má `prev_interval=current_interval=5`; tím se vylučuje jen prostá změna deklarovaného intervalu na hraně, nikoli odlišení odstávky, poruchy, exportní mezery nebo ztracených měření.",
    "- Roční počty: " + ", ".join(f"{year}: {n}" for year, n in sorted(by_year.items(), key=lambda x: int(x[0])) ) + ".",
    "- Jediná >=90denní delta je 2011-08-15T20:05:00Z → 2012-03-01T09:25:00Z, 198 d 13 h 20 min; přechází rok a zůstává neklasifikovaná.",
    "- Kandidáty 2018 Q1 a diagnostického 2021 výřez výslovně označuje v CSV; žádná data nebyla měněna ani rekonstruována.", "",
    "## Rozhodnutí / další validace", "",
    "Délku delty nelze převést na počet chybějících měření bez doložené provozní epochy, pravidel intervalu, timestampové sémantiky a servisní evidence. Všechny případy vyžadují odborné posouzení před jakoukoli modelovou rekonstrukcí. ER-01 a ER-02 zůstávají otevřené; nezávislé auditní etapy pokračují.", "",
    "Výřez: `reports/2026-11-12-long-gap-cases-ge-1d.csv`.",
]
out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"catalog={len(rows)} long_ge_1d={len(long)} ge_7d={long7} ge_90d={long90} interval_pairs={dict(by_interval)}")
print(f"year_counts={dict(sorted(by_year.items(), key=lambda x: int(x[0])))}")
print(out_csv)
print(out_md)
