#!/usr/bin/env python3
"""Validate the targeted corrections required by the independent v3 review."""
import csv, json, subprocess, sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
run = lambda *args: subprocess.run([sys.executable, *map(str, args)], cwd=R, check=True)

registry = json.loads((R/'config/active_proposal_registry.json').read_text())
packages = {p['package_id']: p for p in registry['packages'] if p['status']=='ACTIVE'}
assert packages['p3-temperature-v2.1']['local_validation']['command'] == 'python3 proposals/estimated_short_temperature_gaps_v2/validate.py'
assert packages['restored-source-only-2013-july-pilot']['local_validation']['command'] == 'python3 proposals/restored_source_only_2013_july_pilot/validate.py'
assert all(p['user_approval']=='NOT_APPROVED' and p['actual_weather_mcp_dry_run']=='NOT_RUN' and p['actual_application']=='NOT_APPLIED' for p in packages.values())

p3 = R/'proposals/estimated_short_temperature_gaps_v2'
sim = json.loads((p3/'offline_simulation_v2_1.json').read_text())
assert sim['operations']==21 and sim['episodes']==13 and sim['episode_split'] is False
assert 'SUPERSEDED' in (R/'scripts/simulate_p3_source_first_v2.py').read_text().splitlines()[1]
assert 'SUPERSEDED' in (R/'scripts/reproduce_p3_v2_clean.py').read_text().splitlines()[1]

pilot20 = R/'proposals/restored_source_only_2020_isolated_outtemp'
presence = json.loads((pilot20/'per_target_archive_presence.json').read_text())
expected = {'loucka_reconstruction':0,'pocasi-loucka.eu':0,'pocasi-loucka.eu_GW1000':0,'pocasi-loucka.eu_old':0,'old_weewx':29,'weewx_WH1080':29}
assert presence['archive_presence_counts']==expected
assert len(presence['targets'])==29
assert all(not x['target_row_absent_from_all_archives'] for x in presence['targets'])
assert all(x['target_row_presence_by_archive']=={k: bool(expected[k]) for k in expected} for x in presence['targets'])
decisions = list(csv.DictReader((pilot20/'review_required_candidate_decisions.csv').open()))
assert len(decisions)==2
assert {x['utc'] for x in decisions} == {'2020-02-22T10:40:00Z','2020-08-02T16:10:00Z'}
assert all(x['disposition'].startswith('REVIEW_REQUIRED') for x in decisions)
readme=(pilot20/'README.md').read_text()
assert '2020-02-22 15:00' in readme and '2020-07-10 21:40' in readme

pilot13 = json.loads((R/'proposals/restored_source_only_2013_july_pilot/candidate_metadata.json').read_text())
assert '600' in json.dumps(pilot13) and 'interval' in json.dumps(pilot13)
pilot18 = json.loads((R/'proposals/restored_source_only_2018_dec31_primary/corrections.json').read_text())
assert len(pilot18)==7 and all('RESTORED' in x['reason'] and 'MODERATE' in x['reason'] for x in pilot18)

run(R/'scripts/validate_active_proposal_deduplication.py')
run(R/'proposals/estimated_short_temperature_gaps_v2/validate.py')
run(R/'proposals/restored_source_only_2013_july_pilot/validate.py')
run(R/'scripts/validate_2018_dec31_restored_update_pilot.py')
run(R/'proposals/restored_source_only_2020_isolated_outtemp/validate.py')
run(R/'proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py','--output','/tmp/p3_v2_1_review_simulation.json')

print(json.dumps({'status':'PASS','p3_v2_1_operations':21,'p3_v2_1_episodes':13,'source_rows_2020':expected,'pilot_2020_active':27,'pilot_2020_review_required':2,'pilot_2013_interval_minutes':5,'pilot_2013_observed_cadence_seconds':600,'pilot_2018_reason_provenance':'7/7 RESTORED/MODERATE','database_access':'NONE','mcp_dry_run':'NOT_RUN','staging':False,'application':False},indent=2))
