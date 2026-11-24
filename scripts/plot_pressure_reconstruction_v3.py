#!/usr/bin/env python3
"""Render a standalone SVG summary of V3 temporal and epoch validation."""
import argparse,json
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backtest',type=Path,required=True);ap.add_argument('--temporal',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();b=json.loads(a.backtest.read_text());t=json.loads(a.temporal.read_text())
 W,H=1000,620; parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">','<rect width="100%" height="100%" fill="white"/>','<style>text{font-family:Arial,sans-serif;fill:#202124}.title{font-size:22px;font-weight:bold}.sub{font-size:14px}.axis{stroke:#777;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}.line{fill:none;stroke-width:3}.legend{font-size:13px}</style>','<text x="35" y="32" class="title">Pressure reconstruction V3 — masked controls</text>']
 # upper annual model MAE
 x0,y0,w,h=75,82,850,205;parts.append('<text x="75" y="65" class="sub">Annual masked-control MAE against stored Loučka pressure (hPa)</text>')
 years=sorted(int(y) for y in b['annual_competing_source_scores']); ymax=7
 for i in range(8):
  y=y0+h-i*h/7; val=i
  parts += [f'<line x1="{x0}" y1="{y:.1f}" x2="{x0+w}" y2="{y:.1f}" class="grid"/>',f'<text x="42" y="{y+4:.1f}" font-size="11">{val}</text>']
 for j,year in enumerate(years):
  x=x0+j*w/(len(years)-1);parts.append(f'<text x="{x-12:.1f}" y="{y0+h+18}" font-size="10">{year}</text>')
 colors={'local_barometer_v1':'#167d3f','era5_hourly':'#3867c8','chmi10':'#bb5511'}
 for name,color in colors.items():
  pts=[]
  for j,year in enumerate(years):
   v=b['annual_competing_source_scores'][str(year)]['models'].get(name)
   if not v or v['mae_hpa'] is None:continue
   x=x0+j*w/(len(years)-1);y=y0+h-min(v['mae_hpa'],ymax)*h/ymax;pts.append((x,y))
  if pts:
   parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" stroke="{color}" class="line"/>')
   parts.extend(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>' for x,y in pts)
 # gap length chart
 gx,gy,gw,gh=75,370,850,175;parts.append('<text x="75" y="343" class="sub">Holdout synthetic-gap MAE by gap length (all seasons, years 2023–2025)</text>')
 lengths=b['gap_lengths_seconds'];labels=['5m','30m','1h','6h','1d','3d','14d','28d'];gmax=6
 for i in range(7):
  y=gy+gh-i*gh/6;parts += [f'<line x1="{gx}" y1="{y:.1f}" x2="{gx+gw}" y2="{y:.1f}" class="grid"/>',f'<text x="43" y="{y+4:.1f}" font-size="11">{i}</text>']
 for j,(dur,label) in enumerate(zip(lengths,labels)):
  x=gx+j*gw/(len(lengths)-1);parts.append(f'<text x="{x-12:.1f}" y="{gy+gh+18}" font-size="11">{label}</text>')
 for name,color in [('local_barometer_v1','#167d3f'),('era5_hourly','#3867c8'),('chmi10','#bb5511')]:
  pts=[]
  for j,dur in enumerate(lengths):
   rows=[v for k,v in b['holdout_gap_metrics'].items() if k.startswith(name+'|'+str(dur)+'|')]
   n=sum(v['n'] for v in rows)
   if not n:continue
   mae=sum(v['n']*v['mae_hpa'] for v in rows)/n;x=gx+j*gw/(len(lengths)-1);y=gy+gh-min(mae,gmax)*gh/gmax;pts.append((x,y))
  if pts:parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" stroke="{color}" class="line"/>')
 # legend and temporal compare
 labels2=[('Local barometer V1','#167d3f'),('ERA5 hourly','#3867c8'),('ČHMÚ 10min transferred','#bb5511')]
 for i,(lab,col) in enumerate(labels2):
  xx=90+i*250;parts += [f'<line x1="{xx}" y1="580" x2="{xx+28}" y2="580" stroke="{col}" class="line"/>',f'<text x="{xx+36}" y="585" class="legend">{lab}</text>']
 parts.append('<text x="75" y="605" font-size="12">Separate temporal-only paired test: 10-minute local anchors MAE 0.053–0.056 hPa vs hourly anchors 0.085–0.091 hPa; this is not long-gap transfer accuracy.</text>')
 parts.append('</svg>');a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text('\n'.join(parts)+'\n')
if __name__=='__main__':main()
