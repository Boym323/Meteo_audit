#!/usr/bin/env python3
"""Verify byte identity, source metadata and P_hm presence in the frozen CHMI cache."""
import hashlib,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data/chmi-2026-synop-pressure/manifest.json'

def main():
    doc=json.loads(MANIFEST.read_text(encoding='utf-8'));seen=set();total=0;quality_counts=Counter()
    if doc.get('schema')!='loucka-chmi-synop-pressure-reference-cache-v1':raise SystemExit('Unexpected cache schema')
    for item in doc['files']:
        p=ROOT/item['path'];raw=p.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise SystemExit(f'Cache SHA-256 mismatch: {item["path"]}')
        if item['period'] in seen:raise SystemExit('Duplicate period')
        seen.add(item['period']);data=json.loads(raw)['data']['data']['values']
        rows=[r for r in data if r[0]==item['station']['station_id'] and r[1]=='P_hm']
        if len(rows)!=item['row_count']:raise SystemExit(f'P_hm row count mismatch for {item["period"]}')
        quality_counts.update(str(r[5]) for r in rows)
        total+=sum(r[5] in (0,0.0) for r in rows)
    if seen!={'2026-01','2026-02'}:raise SystemExit(f'Unexpected cached periods: {seen}')
    print(json.dumps({'files_verified':len(seen),'quality_zero_p_hm_rows':total,'all_quality_counts':dict(quality_counts),'manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
