#!/usr/bin/env python3
"""Validate compact annual stable-cadence run aggregates from bounded SQL."""
import csv
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CSV=ROOT/'reports/2026-11-12-candidate-cadence-runs-by-year.csv'
REPORT=ROOT/'reports/2026-11-12-candidate-cadence-runs-by-year.md'
with CSV.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
assert rows and all(2009<=int(r['utc_year'])<=2026 for r in rows)
assert len({(r['utc_year'],r['interval_min'],r['duration_band']) for r in rows})==len(rows)
assert set(r['duration_band'] for r in rows)<= {'lt_1h','1h_to_24h','ge_24h'}
assert set(r['interval_min'] for r in rows)<={'5','30'}
total_runs=sum(int(r['run_count']) for r in rows)
total_edges=sum(int(r['regular_edges']) for r in rows)
assert total_runs==7299
assert total_edges==1661559
by_interval=Counter()
by_band=Counter()
for r in rows:
 by_interval[r['interval_min']]+=int(r['regular_edges'])
 by_band[r['duration_band']]+=int(r['regular_edges'])
longest=max(rows,key=lambda r:int(r['max_run_edges']))
assert by_interval==Counter({'5':1661557,'30':2})
assert int(longest['utc_year'])==2014 and int(longest['max_run_edges'])==29639
regular_duration=int(longest['max_run_edges'])*int(longest['interval_min'])*60
assert regular_duration==8891700
REPORT.write_text(f"""# Kandidátní stabilní kadence podle UTC roku

## Definice a metoda

Bounded read-only SQL byl spuštěn samostatně pro každý UTC rok 2009–2026; ke každému období se přidal nanejvýš přesný předchozí záznam. „Pravidelná hrana“ zde znamená, že interval obou krajních řádků je stejný a delta timestampů přesně odpovídá tomuto intervalu. „Run segment“ je nepřerušená sekvence takových hran. Roční hranice sekvenci přerušuje pro účely výstupu; jde tedy o kandidátní úseky cadence, nikoli automaticky o celou fyzickou/provozní epochu. Délkové pásmo se odvozuje z počtu pravidelných hran × uložené minuty.

## Výsledek a reconciliace

- {total_runs:,} ročních kandidátních run segmentů obsahuje {total_edges:,} přesných pravidelných hran. To přesně odpovídá dřívějšímu agregátu „stejný předchozí i aktuální krok“.
- Interval 5 min tvoří {by_interval['5']:,} hran; interval 30 min dvě hrany. V tomto přísném kritériu se žádná stabilní hrana neobjevuje pro `interval=6`, přestože archive má 2 090 řádků s touto hodnotou. Samotné metadata `interval=6` tedy nedokládá souvislý šestiminutový provoz; konkrétní historická sémantika zůstává neověřena.
- Nejdelší přesně pravidelný run uvnitř jednoho UTC roku je {int(longest['max_run_edges']):,} hran v roce {longest['utc_year']} při 5 min = {regular_duration:,} s (102 d 21 h 55 min). Roční výřez může fyzicky pokračující run rozdělit na hranici roku.
- Počty regular edges podle délky segmentu: <1 h {by_band['lt_1h']:,}; 1–<24 h {by_band['1h_to_24h']:,}; ≥24 h {by_band['ge_24h']:,}.

Roční agregace: `reports/2026-11-12-candidate-cadence-runs-by-year.csv`; reprodukční SQL template: `sql/readonly/stable_cadence_runs_by_year.sql`; lokální checks: `scripts/validate_candidate_cadence_runs.py`.

## Omezení

Cadence přesná s uloženým intervalem není důkaz senzoru/provozu, nezávislosti měření, ani vyloučení ztracených dat mimo pravidelné sekvence. Jednorázové či krátké intervalové hodnoty a timestampové/driver konvence vyžadují odbornou kontrolu. Q1 2018 je v aktuálním živém archivu průběžné, 2021 diagnostický, 2026 neúplný. Výpočet neurčuje příčinu dlouhých přerušení a nevytváří korekční návrhy.
""",encoding='utf-8')
print(f'groups={len(rows)} runs={total_runs} regular_edges={total_edges} by_interval={dict(by_interval)} longest_edges={longest["max_run_edges"]} longest_sec={regular_duration}')
