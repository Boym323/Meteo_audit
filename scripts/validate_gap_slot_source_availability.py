#!/usr/bin/env python3
"""Validate and summarize exact-time source rows intersecting gap slots.

Offline only; consumes the aggregate JSON saved from read-only Weather MCP queries.
"""
from __future__ import annotations
import csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
summary=json.loads((ROOT/'data/p1p2_source_gap_overlay_summary.json').read_text())
aggregate=json.loads((ROOT/'data/p1p2_source_gap_overlay_aggregate.json').read_text())
errors=[]; result_files=sorted((ROOT/'data').glob('p1p2_source_gap_overlay_results_*.json'))
chunks=summary['query_chunks']
if len(chunks)!=103: errors.append(f'expected 103 query chunks; got {len(chunks)}')
if len(result_files)!=len(chunks): errors.append(f'result count {len(result_files)} != chunk count {len(chunks)}')
allowed=set(summary['source_archives'])
fields=summary['fields']
counts=Counter(); years=Counter()
for q in chunks:
 p=ROOT/q['sql']
 if not p.is_file(): errors.append(f'missing SQL {q["sql"]}');continue
 data=p.read_bytes()
 if hashlib.sha256(data).hexdigest()!=q['sql_sha256'] or len(data)!=q['sql_bytes']:errors.append(f'SQL hash/size mismatch {q["sql"]}')
 sql=data.decode()
 cleaned=re.sub(r'--[^\n]*','',sql).strip().lower()
 if not cleaned.startswith('--') and not cleaned.startswith('with'):errors.append(f'non-SELECT query start {q["sql"]}')
 if re.search(r'\b(insert|update|delete|replace|alter|drop|truncate|create)\b',cleaned):errors.append(f'write/DDL token in {q["sql"]}')
 if '1609459200' in sql:errors.append('protected 2021 epoch appears as explicit target bound')
for f in result_files:
 m=re.search(r'results_(\d{4})_(\d{3})\.json$',f.name)
 if not m:errors.append(f'unexpected result filename {f.name}');continue
 doc=json.loads(f.read_text()); rows=doc.get('result')
 if not isinstance(rows,list):errors.append(f'missing result list {f.name}');continue
 for r in rows:
  if r.get('source_database') not in allowed:errors.append(f'unknown source db in {f.name}')
  if r.get('protection_scope')=='PROTECTED_Q1_2018_DIAGNOSTIC' and m.group(1)!='2018':errors.append(f'Q1 guard label outside 2018 in {f.name}')
  if r.get('protection_scope')=='NORMAL' and m.group(1)=='2018':
   # Normal rows are permissible in other 2018 seasons; Q1 was separately labeled.
   pass
  if int(r['source_archive_rows'])<int(r['unique_target_timestamps']):errors.append(f'rows < unique timestamps in {f.name}')
  for field in fields:
   n=int(r[f'{field}_nonnull'])
   if n<0 or n>int(r['source_archive_rows']):errors.append(f'bad non-null count {field} {f.name}')
  counts[(m.group(1),r['source_database'])]+=int(r['source_archive_rows'])
  years[m.group(1)]+=int(r['source_archive_rows'])
if aggregate['summary']['query_chunks']!=103:errors.append('aggregate query_count mismatch')
if aggregate['summary']['candidate_slots']!=153945:errors.append('candidate slot denominator changed unexpectedly')
if aggregate['summary']['source_target_timestamps_sum_per_archive'].get('old_weewx')!=44393:errors.append('old_weewx total mismatch')
if aggregate['summary']['source_target_timestamps_sum_per_archive'].get('weewx_WH1080')!=44406:errors.append('WH1080 total mismatch')
if errors:
 print(json.dumps({'status':'FAIL','errors':errors},indent=2));raise SystemExit(1)
by_db=Counter()
for (_,db),n in counts.items():by_db[db]+=n
print(json.dumps({'status':'PASS','query_chunks':len(chunks),'result_files':len(result_files),'nonempty_query_count':sum(bool(json.loads(p.read_text()).get('result')) for p in result_files),'aggregate_rows':aggregate['summary']['group_rows'],'conditional_slots':aggregate['summary']['candidate_slots'],'source_rows_by_database':dict(by_db)},indent=2))
