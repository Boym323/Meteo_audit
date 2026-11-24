#!/usr/bin/env python3
"""Write a dependency-free SVG comparison plot from v2 validation JSON."""
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--validation',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=json.loads(a.validation.read_text())
    months=[f'2022-{m:02d}' for m in range(1,8)];models={'ERA5 surface':'era5_surface','V1 barometer + T':'v1_frozen_temp','50/50 blend':'blend_50','CHMI LOO':'chmi_regional_loo'}
    colors=['#1769aa','#c64b24','#2e8540','#7a3e9d'];width,height=980,500;left,right,top,bottom=90,35,75,100;plotw=width-left-right;ploth=height-top-bottom; ymax=4.0
    def x(i):return left+i*plotw/(len(months)-1)
    def y(v):return top+ploth*(1-min(ymax,max(0,v))/ymax)
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="980" height="500" viewBox="0 0 980 500">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:Arial,sans-serif;fill:#202124}.title{font-size:21px;font-weight:bold}.small{font-size:12px}.axis{font-size:13px}</style>','<text x="90" y="32" class="title">Loučka pressure models: held-out 2022 exact-hour MAE</text>']
    for tick in range(0,5):
        yy=y(tick);s.append(f'<line x1="{left}" y1="{yy}" x2="{width-right}" y2="{yy}" stroke="#ddd"/>');s.append(f'<text x="{left-12}" y="{yy+4}" text-anchor="end" class="axis">{tick}</text>')
    s.append(f'<line x1="{left}" y1="{y(2)}" x2="{width-right}" y2="{y(2)}" stroke="#333" stroke-dasharray="7 5"/>')
    s.append(f'<text x="{width-right-3}" y="{y(2)-7}" text-anchor="end" class="small">fixed MAE limit 2 hPa</text>')
    for i,m in enumerate(months):s.append(f'<text x="{x(i)}" y="{top+ploth+25}" text-anchor="middle" class="axis">{m[5:]}</text>')
    s.append(f'<text x="23" y="{top+ploth/2}" transform="rotate(-90 23 {top+ploth/2})" text-anchor="middle" class="axis">max(Holešov, Mošnov) MAE (hPa)</text>')
    for (label,key),color in zip(models.items(),colors):
        pts=[]
        for i,m in enumerate(months):
            g=d['test_monthly'].get(m,{}).get('models',{}).get(key)
            if not g:continue
            vals=[q['mae_hpa'] for q in g['scores'].values() if q['mae_hpa'] is not None]
            if vals:pts.append((i,max(vals)))
        if pts:
            path=' '.join((f'{x(i)},{y(v)}' for i,v in pts));s.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="3"/>')
            for i,v in pts:s.append(f'<circle cx="{x(i)}" cy="{y(v)}" r="4" fill="{color}"/>')
        s.append(f'<line x1="{left+20+(list(models).index(label)%2)*260}" y1="{height-64-(list(models).index(label)//2)*22}" x2="{left+48+(list(models).index(label)%2)*260}" y2="{height-64-(list(models).index(label)//2)*22}" stroke="{color}" stroke-width="3"/><text x="{left+55+(list(models).index(label)%2)*260}" y="{height-60-(list(models).index(label)//2)*22}" class="small">{label}</text>')
    s.append('<text x="90" y="475" class="small">Regional/hourly diagnostics only; a pass also requires P95, median bias, reference count and coverage limits.</text>');s.append('</svg>');a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text('\n'.join(s)+'\n')
if __name__=='__main__':main()
