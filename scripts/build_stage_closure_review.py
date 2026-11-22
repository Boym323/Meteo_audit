#!/usr/bin/env python3
"""Render a bounded closeout review for the previously prioritized stages."""
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'PROGRESS.json').read_text())
stages={x['id']:x for x in P['stages']}
checks={
 'A':('COMPLETED_WITH_LIMITATIONS','39/39 defined subtasks verified. Inventory snapshots, per-archive/field aggregates and the source-only cohorts are reproducible. Limitation: 207,182 source-only timestamps are grouped and selected cohorts reviewed; this is not a complete row-by-row meteorological correctness certification.'),
 'I':('COMPLETED_WITH_LIMITATIONS','5/5 defined subtasks verified. Read-only history/current-target reconciliation covers all 65 active operations across 56 timestamps. Limitation: audit history cannot establish pre-audit deletion or mutation.'),
 'L':('IN_PROGRESS','9/10 defined subtasks verified. Active proposal inventory is deduplicated and package-local validations are available. L3 remains open because the broad source-only row/field eligibility gates and removal-cause grouping are incomplete.'),
 'M':('COMPLETED_WITH_LIMITATIONS','6/6 defined subtasks verified. Offline simulators cover active packages and insert/update dependency semantics. Limitation: actual Weather MCP multi-operation behavior is explicitly NOT_RUN.'),
 'N':('COMPLETED_WITH_LIMITATIONS','8/8 defined subtasks verified. Clean-extract and deterministic bundle validations are reproducible. Limitation: N4 extraction utility has not been exercised against the protected live DB adapter; no live query was issued through it.')}
for sid,(state,_) in checks.items():
 assert stages[sid]['status']==state,(sid,stages[sid]['status'],state)
 out=stages[sid]['verified_subtasks']; total=stages[sid]['defined_subtasks']
 if sid in ('A','I','M','N'): assert out==total
now=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
lines=['# Review podmínek uzavření etap A, I, L, M a N','',f'Provedeno UTC: `{now}`. Rozsah GOALu a počet podúkolů nebyl změněn. Review vychází z aktuálního `PROGRESS.json` a ověřených výstupů; nenahrazuje validaci kvality každého historického měření.','']
for sid,(state,reason) in checks.items():
 s=stages[sid]
 lines += [f'## Etapa {sid} — {s["name"]}', '',f'- Stav: **{state}** ({s["verified_subtasks"]}/{s["defined_subtasks"]} podúkolů).',f'- Rozhodnutí: {reason}','']
lines += ['## Závěr','', 'A, I, M a N splňují definované analytické podúkoly a zůstávají `COMPLETED_WITH_LIMITATIONS` kvůli přesně vymezeným omezením. L nelze uzavřít: zbývající L3 je věcnou podmínkou source-first eligibility a stále se zpracovává. Toto review nepovoluje žádnou korekci, MCP dry-run ani změnu rozsahu.']
(ROOT/'reports/2026-11-14-stage-closure-review-A-I-L-M-N.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','timestamp_utc':now,'stages_reviewed':list(checks),'closed_limited':['A','I','M','N'],'still_in_progress':['L'],'scope_changes':0},indent=2))
