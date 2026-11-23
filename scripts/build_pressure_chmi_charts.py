#!/usr/bin/env python3
"""Build dependency-free SVG plots and robust monthly change-point flags."""
import csv
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'reports/parallel-audit/pressure-chmi-numeric-2009-2026'

def read(name):
    with (DATA/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def svg_chart(series, title, subtitle, out, y_min=None, y_max=None):
    W,H=1200,600; L,R,T,B=78,30,66,80; pw,ph=W-L-R,H-T-B
    vals=[float(v) for s in series for _,v,_ in s['points']]
    ymin=y_min if y_min is not None else min(vals); ymax=y_max if y_max is not None else max(vals)
    if ymax<=ymin:ymax=ymin+1
    xmin=min(x for s in series for x,_,_ in s['points']);xmax=max(x for s in series for x,_,_ in s['points'])
    if xmax<=xmin:xmax=xmin+1
    def X(x):return L+(x-xmin)/(xmax-xmin)*pw
    def Y(y):return T+(ymax-y)/(ymax-ymin)*ph
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<rect width="100%" height="100%" fill="#fff"/>',
           f'<text x="{L}" y="30" font-size="22" font-family="sans-serif" font-weight="bold">{title}</text>',
           f'<text x="{L}" y="52" font-size="13" font-family="sans-serif" fill="#444">{subtitle}</text>']
    for i in range(6):
        y=ymin+(ymax-ymin)*i/5; yy=Y(y)
        parts += [f'<line x1="{L}" y1="{yy:.1f}" x2="{W-R}" y2="{yy:.1f}" stroke="#ddd"/>',
                  f'<text x="{L-10}" y="{yy+4:.1f}" text-anchor="end" font-size="12" font-family="sans-serif">{y:.1f}</text>']
    years=range(xmin//12, xmax//12+1)
    for y in years:
        x=X(y*12+6);parts += [f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{H-B}" stroke="#eee"/>',
                               f'<text x="{x:.1f}" y="{H-B+22}" text-anchor="middle" font-size="12" font-family="sans-serif">{y}</text>']
    for s in series:
        coords=' '.join(f'{X(x):.1f},{Y(v):.1f}' for x,v,_ in s['points'])
        dash=' stroke-dasharray="6 4"' if s.get('dash') else ''
        parts.append(f'<polyline fill="none" stroke="{s["color"]}" stroke-width="2"{dash} points="{coords}"/>')
        for x,v,n in s['points']:
            parts.append(f'<circle cx="{X(x):.1f}" cy="{Y(v):.1f}" r="2.3" fill="{s["color"]}"><title>{x//12}-{(x%12):02d}: median {v:.2f} hPa, n={n}</title></circle>')
    lx=L;ly=H-20
    for s in series:
        parts += [f'<line x1="{lx}" y1="{ly-4}" x2="{lx+28}" y2="{ly-4}" stroke="{s["color"]}" stroke-width="3"/>',
                  f'<text x="{lx+34}" y="{ly}" font-size="12" font-family="sans-serif">{s["label"]}</text>']
        lx+=min(340,40+len(s['label'])*7)
    parts += [f'<text x="{W/2}" y="{H-2}" text-anchor="middle" font-size="12" font-family="sans-serif">Měsíc UTC (na ose rok)</text>',
              f'<text transform="translate(20,{H/2}) rotate(-90)" text-anchor="middle" font-size="12" font-family="sans-serif">Loučka − ČHMÚ [hPa]</text></svg>']
    (DATA/out).write_text('\n'.join(parts)+'\n',encoding='utf-8')

def main():
    rows=read('hourly_monthly_stats.csv'); series=[]
    for station,color in [('11774','#1769aa'),('11782','#c62828')]:
        for element,field,label,dash in [('P_hm','barometer','barometer − P_hm',False),('P','pressure','pressure − P',True)]:
            points=[]
            for r in rows:
                if r['station_id'].endswith(station) and r['element']==element and r['loucka_field']==field:
                    points.append((int(r['utc_year'])*12+int(r['month']),float(r['median']),int(r['n'])))
            if points:series.append({'points':points,'color':color,'label':label+(' Holešov' if station=='11774' else ' Mošnov'),'dash':dash})
    svg_chart(series,'ČHMÚ hourly pressure reference vs Loučka archive','Exact UTC timestamp pairs; unadjusted field differences. Stations 11774 / 11782. Only QUALITY=0.',
              'pressure_chmi_hourly_monthly_bias.svg')
    coarse=read('daily_chmi_monthly_context.csv'); dseries=[]
    for station,color in [('11774','#1769aa'),('11782','#c62828')]:
        pts=[]
        for r in coarse:
            if r['station_id'].endswith(station) and r['height_adjusted_pressure_minus_chmi_P_hpa']:
                pts.append((int(r['year'])*12+int(r['month']),float(r['height_adjusted_pressure_minus_chmi_P_hpa']),int(r['chmi_daily_avg_rows'])))
        if pts:dseries.append({'points':pts,'color':color,'label':'height-adjusted pressure − daily P '+('Holešov' if station=='11774' else 'Mošnov'),'dash':False})
    svg_chart(dseries,'Long-run monthly context: Loučka pressure vs daily CHMI P','Monthly medians; UTC date labels are not exact daily-window matches. Elevation transfer is a diagnostic model.',
              'pressure_chmi_daily_context_2009_2026.svg')
    # Change-point flags: pooled station medians for like-for-like fields;
    # flag absolute adjacent-month jumps >= 5 hPa, never auto-classify as repair.
    by= {}
    for r in rows:
        if (r['loucka_field'],r['element']) not in (('barometer','P_hm'),('pressure','P')):continue
        k=(int(r['utc_year']),int(r['month']),r['loucka_field'],r['element'])
        by.setdefault(k,[]).append(float(r['median']))
    pooled={k:statistics.median(v) for k,v in by.items() if len(v)==2}
    out=[]
    for field,element in [('barometer','P_hm'),('pressure','P')]:
        prior=None
        keys=sorted(k for k in pooled if k[2:]==(field,element))
        for k in keys:
            value=pooled[k]
            if prior:
                delta=value-prior[1]
                if abs(delta)>=5:
                    out.append({'period_utc':f'{k[0]}-{k[1]:02d}','pair':f'{field}-{element}','previous_period':f'{prior[0][0]}-{prior[0][1]:02d}',
                                'previous_pooled_median_hpa':prior[1],'pooled_median_hpa':value,'step_hpa':delta,'interpretation':'candidate change point; inspect station-specific series and source epochs'})
            prior=(k,value)
    with (DATA/'change_point_candidates.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]) if out else ['period_utc']);w.writeheader();w.writerows(out)
    print(f'change point candidates: {len(out)}')

if __name__=='__main__':main()
