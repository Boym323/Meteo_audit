import unittest
from collections import defaultdict

from scripts.compare_pressure_reanalysis_v2 import model_scores


class PressureV3ValidationTests(unittest.TestCase):
    def test_model_counts_and_coverage_are_independent_and_pairing_is_exact(self):
        rows=[{"dateTime":0,"barometer":1000.0,"outTemp":5.0},
              {"dateTime":3600,"barometer":None,"outTemp":5.0},
              {"dateTime":7200,"barometer":1000.0,"outTemp":5.0}]
        era={ts:(1000.0,1000.0,5.0) for ts in (0,3600,7200)}
        refs=defaultdict(dict)
        for ts in (0,3600,7200):
            refs[("0-20000-0-11774","P")][ts]=1000.0;refs[("0-20000-0-11782","P")][ts]=1000.0
        gate={"min_common_hours_per_month":1,"min_common_coverage":0.0,"max_mae_hpa":100,"max_p95_absolute_hpa":100,"max_abs_median_bias_hpa":100}
        v1={"training_domain":{"barometer_hpa":[990,1010],"outTemp_c":[-20,30]},"parameters":{"offset_hpa":0,"temperature_slope_hpa_per_c":0,"temperature_center_c":5}}
        scores,_=model_scores(rows,era,100,v1,0,refs,gate,set())
        month=scores["1970-01"]["models"]
        self.assertEqual(month["era5_surface"]["n_eligible_predictions"],3)
        self.assertEqual(month["v1_frozen_temp"]["n_eligible_predictions"],2)
        self.assertEqual(month["blend_50"]["n_eligible_predictions"],2)
        self.assertEqual(month["era5_surface"]["coverage"],1)
        self.assertEqual(month["v1_frozen_temp"]["coverage"],1)
        self.assertEqual(scores["1970-01"]["paired_all_model_timestamps_utc"],[0,7200])
        self.assertEqual(month["v1_frozen_temp"]["scores"]["H"]["n"],2)


if __name__=="__main__":unittest.main()
