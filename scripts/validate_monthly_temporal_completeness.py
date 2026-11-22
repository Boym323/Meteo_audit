#!/usr/bin/env python3
"""Validate and summarize bounded monthly archive cadence aggregates."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/2026-11-12-monthly-temporal-completeness.csv"
ANNUAL_PATH = ROOT / "reports/2026-11-12-annual-temporal-completeness.csv"
REPORT_PATH = ROOT / "reports/2026-11-12-monthly-temporal-completeness.md"
with CSV_PATH.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 212, f"expected 212 UTC months, got {len(rows)}"
keys = [(int(r["utc_year"]), int(r["utc_month"])) for r in rows]
assert len(keys) == len(set(keys)), "duplicate UTC month"
assert keys == sorted(keys), "months not sorted"
# Annotate scope without implying meteorological validity.
for r in rows:
    y, m = int(r["utc_year"]), int(r["utc_month"])
    flags = []
    if y == 2021: flags.append("2021_DIAGNOSTIC_ONLY")
    if y == 2018 and m <= 3: flags.append("2018_Q1_INTERIM_LIVE")
    if y == 2026: flags.append("PARTIAL_CURRENT_ARCHIVE")
    if int(r["archive_rows"]) == 0: flags.append("NO_ARCHIVE_ROWS_CAUSE_UNCLASSIFIED")
    r["review_flags"] = ";".join(flags) if flags else "historical_archive_snapshot"
    n = int(r["archive_rows"]); edges = int(r["edge_count"])
    assert n >= 0 and max(n - 1, 0) <= edges <= n, (r, "edge/row mismatch")
    for k in ("matches_previous_step", "matches_current_step", "exceeds_both_steps", "shorter_than_both_steps", "interval_transitions"):
        v = int(r[k]) if r[k] else 0
        assert 0 <= v <= edges, (r, k)
    if edges:
        assert int(r["min_delta_sec"]) <= int(r["max_delta_sec"])
    else:
        assert not r["min_delta_sec"] and not r["max_delta_sec"]

fields=list(rows[0])
with CSV_PATH.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
by_year=defaultdict(lambda:{k:0 for k in ("archive_rows","edge_count","matches_previous_step","matches_current_step","exceeds_both_steps","shorter_than_both_steps","interval_transitions","empty_months","months_with_data")})
for r in rows:
    y=by_year[int(r["utc_year"])]
    for k in ("archive_rows","edge_count","matches_previous_step","matches_current_step","exceeds_both_steps","shorter_than_both_steps","interval_transitions"):
        y[k]+=int(r[k] or 0)
    y["empty_months"]+=int(int(r["archive_rows"])==0)
    y["months_with_data"]+=int(int(r["archive_rows"])>0)
annual_fields=["utc_year","months_with_data","empty_months","archive_rows","edge_count","matches_previous_step","matches_current_step","exceeds_both_steps","shorter_than_both_steps","interval_transitions","review_flags"]
with ANNUAL_PATH.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=annual_fields);w.writeheader()
    for year,v in sorted(by_year.items()):
        flags=[]
        if year==2021:flags.append("DIAGNOSTIC_ONLY")
        if year==2018:flags.append("Q1_INTERIM_LIVE")
        if year==2026:flags.append("PARTIAL_CURRENT_ARCHIVE")
        w.writerow({"utc_year":year,**v,"review_flags":";".join(flags) or "historical_archive_snapshot"})

# Reconciliation against independently validated exact archive and LAG totals.
assert sum(int(r["archive_rows"]) for r in rows)==1_689_890
assert sum(int(r["edge_count"]) for r in rows)==1_689_889
assert sum(int(r["exceeds_both_steps"] or 0) for r in rows)==24_519
assert sum(int(r["interval_transitions"] or 0) for r in rows)==4_182
assert sum(int(r["shorter_than_both_steps"] or 0) for r in rows)==79
assert sum(int(r["matches_previous_step"] or 0) for r in rows)==1_663_262
assert sum(int(r["matches_current_step"] or 0) for r in rows)==1_663_588
empty=[r for r in rows if int(r["archive_rows"])==0]
assert [(int(r["utc_year"]),int(r["utc_month"])) for r in empty]==[(2011,m) for m in range(9,13)]+[(2012,m) for m in range(1,3)]
REPORT_PATH.write_text(f"""# Měsíční a roční časová kontinuita archivu

## Metoda

Read-only bounded UTC epoch dotaz byl spuštěn samostatně pro každý UTC měsíc 2009-03 až 2026-10 (212 měsíců). Dotaz četl řádky uvnitř měsíce a nejvýše jednoho přesného indexed předchůdce před hranicí; `LAG()` počítal každou hranu právě v měsíci jejího pozdějšího endpointu. Očekávaný krok pro diagnostickou shodu je příslušný uložený `interval` v minutách. Metriky předchozí/současný krok se mohou překrývat; nejsou missing-slot počtem. Všechny hranice jsou UTC epochy, nikoli `FROM_UNIXTIME` lokální měsíce.

## Ověřený souhrn

- {len(rows)} měsíců, {sum(int(r['archive_rows']) for r in rows):,} archivních řádků, {sum(int(r['edge_count']) for r in rows):,} sousedních hran; součty se přesně shodují s independentně ověřeným `COUNT(*)` a LAG inventory.
- {sum(int(r['archive_rows'])==0 for r in rows)} úplných UTC měsíců nemá žádný archive row: 2011-09 až 2012-02. Záznamy chybí, ale z tohoto faktu samotného nelze rozlišit odstávku stanice, ztrátu archivu ani jinou příčinu.
- Přes 1 689 889 hran je 24 519 delších než oba sousední uložené intervaly; intervalových přechodů je 4 182. Výsledky reconciliují dříve ověřené celkové intervalové agregáty.
- 2018 Q1 je výslovně označeno jako průběžné/live; 2021 jako diagnostické; 2026 je neúplný live archiv do posledního řádku v říjnu.

Roční souhrn v `reports/2026-11-12-annual-temporal-completeness.csv`; měsíční detail v `reports/2026-11-12-monthly-temporal-completeness.csv`. Reprodukční query template `sql/readonly/monthly_temporal_completeness.sql`; deterministic verifier/aggregator `scripts/validate_monthly_temporal_completeness.py`.

## Omezení

Toto je časová kontinuita řádků v `loucka_reconstruction.archive`. Měsíční nula řádků není automaticky plánovaná odstávka ani potvrzená data loss. U dlouhých delt jsou odhady počtu měření podmíněné nepřerušenou kadencí; bez provozních epoch a externích servisních logů je nelze považovat za očekávané sloty. Výsledek není meteorologická validace hodnot a nepovoluje doplnění. Žádný zápis neproběhl.
""",encoding="utf-8")
print(f"months={len(rows)} years={len(by_year)} rows={sum(int(r['archive_rows']) for r in rows)} edges={sum(int(r['edge_count']) for r in rows)} empty_months={len(empty)} exceeds_both={sum(int(r['exceeds_both_steps'] or 0) for r in rows)} interval_transitions={sum(int(r['interval_transitions'] or 0) for r in rows)}")
for year,v in sorted(by_year.items()):print(f"{year},{v['archive_rows']},{v['edge_count']},{v['empty_months']},{v['exceeds_both_steps']},{v['interval_transitions']}")
