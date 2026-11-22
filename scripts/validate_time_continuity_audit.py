#!/usr/bin/env python3
"""Reconcile the existing continuity snapshots used by TIME_CONTINUITY_AUDIT."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def rows(name: str):
    with (ROOT / 'reports' / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

monthly = rows('2026-11-12-monthly-temporal-completeness.csv')
events = rows('2026-11-12-gap-event-catalog.csv')
bands = rows('2026-11-12-gap-duration-bands.csv')
steps = rows('2026-11-12-interval-step-relations.csv')
runs = rows('2026-11-12-candidate-cadence-runs-by-year.csv')
bridges = rows('2026-11-13-cadence-year-boundary-bridges.csv')
long_gaps = rows('2026-11-12-long-gap-cases-ge-1d.csv')
slots = rows('2026-11-12-long-gap-conditional-5m-slots.csv')
archives = rows('2026-11-13-long-gap-all-archive-availability.csv')

assert len(monthly) == 212
assert sum(int(r['archive_rows']) for r in monthly) == 1_689_890
assert sum(int(r['edge_count']) for r in monthly) == 1_689_889
assert [(r['utc_year'], r['utc_month']) for r in monthly if int(r['archive_rows']) == 0] == [
    ('2011','9'),('2011','10'),('2011','11'),('2011','12'),('2012','1'),('2012','2')]
assert len(events) == 24_523
assert sum(int(r['exceeds_both_steps']) for r in events) == 24_519
assert sum(int(r['matches_either_step']) for r in events) == 4
assert len(bands) == 50
band_counts = {b: sum(int(r['gap_pairs']) for r in bands if r['duration_band'] == b) for b in {r['duration_band'] for r in bands}}
assert band_counts == {'01_lt_1h':23_699,'02_1h_to_lt_1d':780,'03_1d_to_lt_7d':39,'04_7d_to_lt_30d':4,'06_ge_90d':1}
assert len(steps) == 71 and sum(int(r['pairs']) for r in steps) == 1_689_889
assert len(runs) == 55
assert sum(int(r['run_count']) for r in runs) == 7_299
assert sum(int(r['regular_edges']) for r in runs) == 1_661_559
assert sum(int(r['regular_edges']) for r in runs if int(r['interval_min']) == 5) == 1_661_557
assert sum(int(r['regular_edges']) for r in runs if int(r['interval_min']) == 30) == 2
assert len(bridges) == 17 and sum(int(r['annual_runs_joined']) for r in bridges) == 13
assert {r['utc_year'] for r in bridges if r['cross_year_edge_regular'] == '0'} == {'2012','2014','2017','2022'}
assert len(long_gaps) == len(slots) == 44
assert all(r['aligned_to_300s_endpoint_difference'] == 'true' and int(r['delta_mod_300_seconds']) == 0 for r in slots)
assert sum(int(r['conditional_intermediate_5m_slots_if_continuous']) for r in slots) == 97_048
longest = max(slots, key=lambda r: int(r['delta_seconds']))
assert longest['prev_utc'] == '2011-08-15T20:05:00Z' and longest['target_utc'] == '2012-03-01T09:25:00Z'
assert int(longest['delta_seconds']) == 17_155_200
assert int(longest['conditional_intermediate_5m_slots_if_continuous']) == 57_183
src = {r['archive']:r for r in archives}
assert int(src['loucka_reconstruction']['rows_inside_open_gap']) == 0
for name in ('old_weewx','weewx_WH1080'):
    assert int(src[name]['rows_inside_open_gap']) == 3_560
    assert int(src[name]['outTemp_zero']) == 3_264
assert int(src['pocasi-loucka.eu']['rows_inside_open_gap']) == 0
assert int(src['pocasi-loucka.eu_GW1000']['rows_inside_open_gap']) == 0
print('PASS: monthly rows/edges, event catalog, interval relations, cadence runs, year bridges, 44 long gaps and archive availability reconcile')
