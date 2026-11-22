#!/usr/bin/env python3
"""Build a compact field concordance report from read-only SQL aggregates."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'data/annual_secondary_cross_archive_exact_2024_2026.json'
REPORTS=ROOT/'reports'
STEM='2026-11-13-secondary-exact-cross-archive-2024-2026'
def main():
 d=json.loads(INPUT.read_text()); fields=d['fields']; rec=[]; summary=[]
 for y in d['results']:
  year=int(y['year']); n=int(y['production_rows']); pairs=int(y['exact_timestamp_pairs'])
  summary.append({'year':year,'production_rows':n,'exact_timestamp_pairs':pairs,'production_without_reconstruction_row':int(y['production_without_reconstruction_row']),'usUnits_mismatches':int(y['usUnits_mismatches']),'interval_mismatches':int(y['interval_mismatches'])})
  for f in fields:
   rec.append({'year':year,'variable':f,'production_nonnull':int(y[f'{f}__production_nonnull']),'reconstruction_nonnull':int(y[f'{f}__reconstruction_nonnull']),'both_nonnull':int(y[f'{f}__both_nonnull']),'equal_nonnull_values':int(y[f'{f}__equal']),'different_nonnull_values':int(y[f'{f}__different']),'production_only_nonnull':int(y[f'{f}__production_only']),'reconstruction_only_nonnull':int(y[f'{f}__reconstruction_only'])})
 out={'source_database':'pocasi-loucka.eu','target_database':'loucka_reconstruction','fields':len(fields),'summary':summary,'field_results':rec,'interpretation':'Exact archive-copy concordance is verified, but production/reconstruction are not independent measurements.'}
 (REPORTS/f'{STEM}.json').write_text(json.dumps(out,indent=2)+'\n')
 with (REPORTS/f'{STEM}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rec[0]));w.writeheader();w.writerows(rec)
 lines=['# Přesná concordance secondary fields: production vs reconstruction (2024–2026)','',
 'Read-only exact-`dateTime` porovnání 42 polí. Roky 2024 a 2025 jsou celé UTC roky. Rok 2026 pokrývá pouze rekonstrukční interval od 1. 1. do posledního dostupného cílového timestampu 29. 10. 2026 15:10 UTC. Produkční archiv je zdrojový/překryvný archiv, nikoli nezávislé fyzické měření.', '',
 '| Rok/okno | Production rows | Přesné timestamp páry | Bez cílového řádku | `usUnits` rozdíl | `interval` rozdíl |','|---|---:|---:|---:|---:|---:|']
 for s in summary:
  label=str(s['year']) if s['year']<2026 else '2026 do 29. 10. 15:10Z'
  lines.append(f"| {label} | {s['production_rows']:,} | {s['exact_timestamp_pairs']:,} | {s['production_without_reconstruction_row']} | {s['usUnits_mismatches']} | {s['interval_mismatches']} |".replace(',',' '))
 diffs=sum(x['different_nonnull_values'] for x in rec); one_side=sum(x['production_only_nonnull']+x['reconstruction_only_nonnull'] for x in rec)
 lines += ['',f"Ve {len(fields)} polích za tři okna je celkem {diffs} rozdílných porovnatelných non-NULL hodnot a {one_side} jednostranných non-NULL případů. Per-field counts jsou v `{STEM}.csv`; agregovaný výsledek `{STEM}.json`; reprodukční SQL `sql/readonly/annual_secondary_cross_archive_exact_2024_2026.sql`.",'',
 'Shoda potvrzuje kopii/provenienční překryv mezi hlavním produkčním archivem a rekonstrukcí; nejde o nezávislé ověření fyzikální správnosti. Nezjištěná neshoda neprokazuje kvalitu společného upstream měření. 2026 je partial; výsledky nejsou dostupnostní ani klimatický trend.']
 (REPORTS/f'{STEM}.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
