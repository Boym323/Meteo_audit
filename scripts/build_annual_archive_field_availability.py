#!/usr/bin/env python3
"""Build a deterministic long-form availability matrix from annual SQL aggregates."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/tmp/annual_allfields_result.json')
OUT = ROOT / 'reports'


def main():
    payload = json.loads(SOURCE.read_text())
    fields = payload['fields']
    records = []
    for year_row in payload['results']:
        year = int(year_row['year'])
        total = int(year_row['archive_rows'])
        for field in fields:
            nulls = int(year_row[f'{field}__null'])
            nonnull = int(year_row[f'{field}__nonnull'])
            records.append({
                'year': year,
                'variable': field,
                'archive_rows': total,
                'null_rows': nulls,
                'nonnull_rows': nonnull,
                'null_share': nulls / total if total else None,
            })
    years = [int(x['year']) for x in payload['results']]
    summary = {
        'database': 'loucka_reconstruction',
        'period': 'UTC calendar years 2009–2026; 2026 is partial through latest available archive row',
        'fields_count': len(fields),
        'years': years,
        'year_row_counts': {str(x['year']): int(x['archive_rows']) for x in payload['results']},
        'records': records,
    }
    timelines = []
    for field in fields:
        observed = [int(x['year']) for x in payload['results'] if int(x[f'{field}__nonnull']) > 0]
        timelines.append({
            'variable': field,
            'first_nonnull_year_observed': min(observed) if observed else None,
            'last_nonnull_year_observed': max(observed) if observed else None,
            'years_with_any_nonnull': len(observed),
            'scope': 'archive availability only; not sensor installation or operational period',
        })
    stem = '2026-11-13-annual-archive-field-availability-2009-2026'
    with (OUT / f'{stem}.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)
    (OUT / f'{stem}.json').write_text(json.dumps(summary, indent=2) + '\n')
    with (OUT / '2026-11-13-archive-field-observed-year-span.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(timelines[0]))
        w.writeheader()
        w.writerows(timelines)
    lines = [
        '# Roční dostupnost číselných polí archivu — 2009 až 2026', '',
        'Read-only roční souhrny pokrývají všech 77 číselných polí `loucka_reconstruction.archive` v 18 UTC kalendářních letech. Jmenovatelem je počet existujících řádků archivu; nejde o očekávané měřicí sloty, dobu provozu senzoru ani úplnost měření. Rok 2026 je partial. Rok 2021 je zahrnut pouze diagnosticky a bez korekčních návrhů. Jeden široký celohistorický dotaz překročil `max_statement_time`; stejný výpočet byl rozdělen do 18 indexovaných UTC ročních rozsahů a všechny doběhly.', '',
        '| Rok | Řádky archivu | Pole celoročně NULL | Pole bez NULL |', '|---:|---:|---:|---:|'
    ]
    for x in payload['results']:
        y = int(x['year']); n = int(x['archive_rows'])
        all_null = sum(int(x[f'{f}__nonnull']) == 0 for f in fields)
        no_null = sum(int(x[f'{f}__null']) == 0 for f in fields)
        lines.append(f'| {y} | {n:,} | {all_null} | {no_null} |'.replace(',', ' '))
    lines += ['', f'Long-form CSV: `{stem}.csv`; strojový výstup: `{stem}.json`; rozsah prvního/posledního pozorovaného non-NULL roku: `2026-11-13-archive-field-observed-year-span.csv`; reprodukční SQL: `sql/readonly/annual_archive_field_availability_2009_2026.sql`.', '', 'Výsledky jsou inventář archivní dostupnosti, nikoli automatická klasifikace kvality. Zdrojová provenience, fyzická instalace, měřicí intervaly a sezónní očekávanost nejsou odvozovány z NULL poměrů.']
    (OUT / f'{stem}.md').write_text('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
