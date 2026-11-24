import csv
import hashlib
import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

from scripts.audit_pressure_input_qc_v2 import isolated_reversal
from scripts.backtest_pressure_reconstruction_v3 import chmi_predict, load_era5
from scripts.build_pressure_reconstruction_v2 import Q1_START, Q1_END
from scripts.compare_pressure_reanalysis_v2 import model_scores
from scripts.validate_pressure_station_field import transport_station_pressure


class PressureReconstructionV3Tests(unittest.TestCase):
    def test_models_have_own_prediction_counts_and_matched_timestamps(self):
        rows=[{"dateTime":0,"barometer":1000.0,"outTemp":5.0},
              {"dateTime":3600,"barometer":None,"outTemp":5.0},
              {"dateTime":7200,"barometer":1000.0,"outTemp":5.0}]
        era={ts:(1000.0,1000.0,5.0) for ts in (0,3600,7200)}
        refs=defaultdict(dict)
        for ts in (0,3600,7200):
            refs[("0-20000-0-11774","P")][ts]=1000.0
            refs[("0-20000-0-11782","P")][ts]=1000.0
        gate={"min_common_hours_per_month":1,"min_common_coverage":0.0,"max_mae_hpa":100,"max_p95_absolute_hpa":100,"max_abs_median_bias_hpa":100}
        v1={"training_domain":{"barometer_hpa":[990,1010],"outTemp_c":[-20,30]},"parameters":{"offset_hpa":0,"temperature_slope_hpa_per_c":0,"temperature_center_c":5}}
        result,_=model_scores(rows,era,100,v1,0,refs,gate,set());month=result['1970-01']['models']
        self.assertEqual(month['era5_surface']['n_eligible_predictions'],3)
        self.assertEqual(month['v1_frozen_temp']['n_eligible_predictions'],2)
        self.assertEqual(month['blend_50']['n_eligible_predictions'],2)
        self.assertEqual(month['era5_surface']['coverage'],1)
        self.assertEqual(month['v1_frozen_temp']['coverage'],1)
        self.assertEqual(result['1970-01']['paired_all_model_timestamps_utc'],[0,7200])
        self.assertEqual(month['v1_frozen_temp']['scores']['H']['n'],2)

    def test_mosnov_station_height_epoch(self):
        # CHMI meta1: 250.4 m through 2016-05-23, 252.8 m from 2016-05-24.
        old=transport_station_pressure(1000,10,425,250.4)
        new=transport_station_pressure(1000,10,425,252.8)
        self.assertLess(old,new)
        self.assertAlmostEqual(new-old,0.284,delta=.02)

    def test_chmi_station_to_loucka_transport_sign_is_physical(self):
        chmi={"H":([0,600],[1000,1000]),"M":([0,600],[1000,1000])}
        value=chmi_predict(300,10,chmi)
        self.assertLess(value,1000)  # Loucka is higher than both reference stations.

    def test_era5_multi_year_files_accumulate_and_hash_is_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);items=[]
            for year,stamp in ((2023,"2023-01-01T00:00"),(2024,"2024-01-01T00:00")):
                name=f"loucka_era5_nearest-{year}.json";body=json.dumps({"elevation":480,"hourly":{"time":[stamp],"surface_pressure":[950.0],"temperature_2m":[5.0]}}).encode();(d/name).write_bytes(body)
                items.append({"file":name,"sha256":hashlib.sha256(body).hexdigest()})
            (d/'manifest.json').write_text(json.dumps({"responses":items}))
            values,_,_=load_era5(d)
            self.assertEqual(len(values['loucka_era5_nearest']),2)
            items[0]['sha256']='0'*64;(d/'manifest.json').write_text(json.dumps({"responses":items}))
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):load_era5(d)

    def test_chmi_ten_minute_linear_is_not_hourly_interpolation(self):
        # Midpoint interpolation should be exact on a locally linear reference.
        chmi={k:([0,600],[1000,1002]) for k in ('H','M')}
        self.assertAlmostEqual(chmi_predict(300,10,chmi),978.6133,delta=.02)


if __name__=='__main__':unittest.main()
