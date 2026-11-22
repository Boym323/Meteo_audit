#!/usr/bin/env python3
import json
from pathlib import Path
p=json.loads(Path('data/source_only_2011_two_outtemp_conflicts.json').read_text())
assert p['summary']=={'candidates':2,'zero_source_values_held':2,'projected_targets_already_present':2,'change_events':0,'correction_operations':0}
for x in p['candidates']:
 assert x['grid_remainder_seconds']==240 and x['offset_seconds']==60 and x['change_history_events']==0
 assert x['source_archives']['weewx_WH1080']['outTemp']==0 and x['source_archives']['old_weewx']['outTemp'] is None
 assert x['other_archive_evidence']['pocasi-loucka.eu_old_exact_source_key_outTemp']==x['other_archive_evidence']['reconstruction_nearest_target_outTemp']
 assert x['correction_operation'] is None and 'HISTORICALLY_REMOVED_SUSPECTED' in x['disposition']
print('PASS: two 2011 one-sided source-temperature zeros held; existing +60s targets and eu_old context documented; no duplicate/shift proposal.')
