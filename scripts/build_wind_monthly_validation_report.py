#!/usr/bin/env python3
"""Render an evidence summary for monthly wind candidate comparisons."""
import json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    d=json.loads((ROOT/'MONTHLY_WIND_REFERENCE_VALIDATION.json').read_text()); rows=d['station_month_results']
    labels={'windSpeed':'Wind speed: Loučka archive windSpeed vs CHMI Fprum',
            'windGust':'Wind gust: Loučka archive windGust vs CHMI Fmax',
            'windDir':'Wind direction: Loučka archive windDir vs CHMI Dprum'}
    grouped=defaultdict(list)
    for r in rows:grouped[r['variable']].append(r)
    lines=['# Měsíční validace větrných kandidátů','',
      f"Zpracováno {d['candidate_count']} individuálních kandidátů ve {d['candidate_period_count']} obdobích; vytvořeno {len(rows)} párování období–stanice. Snapshot `{d['snapshot_id']}`.",'',
      'Srovnání používá přesné UTC časy, pouze CHMI quality 0 a bez interpolace. Loučka rychlosti jsou převedeny z km/h na m/s. Výsledky jsou regionální kontext, ne fyzická validace ani kalibrace.', '',
      '| Veličina | Kandidáti | Měsíc–stanice | UTC páry | Spárováno / kvalitní reference (min.) | Kvalitní reference / očekávané sloty (min.) | Bias reference−Loučka | MAE | RMSE | Korelace |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for variable in ('windSpeed','windGust','windDir'):
        rs=grouped[variable];candidates=d['candidate_counts'][variable];pairs=sum(r['matched_pairs'] for r in rs)
        cover=min((r['matched_coverage_of_valid_reference'] for r in rs),default=0)
        expected_cover=min((r['reference_slot_coverage_of_expected'] for r in rs),default=0)
        if variable=='windDir':
            biasvals=[r['circular_direction_statistics']['circular_bias_reference_minus_loucka_deg'] for r in rs if r['circular_direction_statistics'] and r['matched_pairs']]
            maes=[r['circular_direction_statistics']['circular_mae_deg'] for r in rs if r['circular_direction_statistics'] and r['matched_pairs']]
            bias=f"circular {sum(biasvals)/len(biasvals):.1f}° mean" if biasvals else '—';mae=f"{sum(maes)/len(maes):.1f}° circular" if maes else '—';rmse='—';corr='—'
        else:
            biasvals=[r['bias_reference_minus_loucka'] for r in rs if r['bias_reference_minus_loucka'] is not None]
            maes=[r['mae'] for r in rs if r['mae'] is not None];rmses=[r['rmse'] for r in rs if r['rmse'] is not None];cors=[r['correlation'] for r in rs if r['correlation'] is not None]
            bias=f"{sum(biasvals)/len(biasvals):.3f} m/s" if biasvals else '—';mae=f"{sum(maes)/len(maes):.3f} m/s" if maes else '—';rmse=f"{sum(rmses)/len(rmses):.3f} m/s" if rmses else '—';corr=f"{sum(cors)/len(cors):.3f}" if cors else '—'
        lines.append(f"| {labels[variable]} | {candidates} | {len(rs)} | {pairs:,} | {cover:.2%} | {expected_cover:.2%} | {bias} | {mae} | {rmse} | {corr} |")
    lines += ['', '## Význam a omezení', '',
      '- ČHMÚ popisuje 10minutové prvky D, F, Dprum, Fprum, Dmax, Fmax a Casmax; rozlišení prvků je zachováno v surových záznamech.',
      '- Fprum je 10minutová průměrná rychlost větru; Fmax je prvek maximální rychlosti. Přesné okno lokálního `windGust` ani shoda jeho časové podpory s ČHMÚ Fmax nejsou doloženy.',
      '- Dprum je směrový průměr. Směr se vyhodnocuje kruhově (cirkulární průměr, koncentrace a nejkratší úhlový rozdíl), nikoli aritmetickým průměrem přes hranici 0°/360°.',
      '- Stejný časový štítek neprokazuje stejnou délku intervalu, expoziční podmínky, stanoviště ani snímač. Souřadnice a expozice loučského anemometru nejsou ověřeny.',
      '- Vysoká korelace ani nízký rozdíl samy neodstraňují blokaci provenience nebo fyzické validace. Žádná korekce ani publikační povolení se nevytváří.', '',
      'Všechny detailní řádky, quality counts, hashované soubory, denní a šestihodinové struktury a kruhové statistiky jsou v `MONTHLY_WIND_REFERENCE_VALIDATION.json`.', '',
      '### Zdrojové hashy', '']
    for p,h in sorted(d['reference_file_sha256'].items()):lines.append(f'- `{p}`: `{h}`')
    (ROOT/'WIND_MONTHLY_VALIDATION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'candidate_count':d['candidate_count'],'station_month_rows':len(rows),'report':'WIND_MONTHLY_VALIDATION_REPORT.md'},indent=2))
if __name__=='__main__':main()
