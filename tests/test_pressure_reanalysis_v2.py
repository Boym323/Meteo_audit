import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_pressure_input_qc_v2 import isolated_reversal
from scripts.build_pressure_reconstruction_v2 import combine, Q1_START, Q1_END
from scripts.validate_pressure_station_field import metrics
from scripts.compare_pressure_reanalysis_v2 import load_era5


class PressureReanalysisV2Tests(unittest.TestCase):
    def test_spike_screen_requires_isolated_reversal_and_close_return(self):
        self.assertTrue(isolated_reversal((0,1000.0),(300,1005.5),(600,1000.3)))
        self.assertFalse(isolated_reversal((0,1000.0),(300,1005.5),(600,1002.0)))
        self.assertFalse(isolated_reversal((0,1000.0),(1200,1005.5),(1500,1000.1)))
        self.assertFalse(isolated_reversal((0,1000.0),(300,1002.9),(600,1000.1)))

    def test_metrics_keep_signed_median_bias_and_absolute_p95(self):
        m=metrics([-2.0,1.0,3.0])
        self.assertEqual(m['n'],3)
        self.assertEqual(m['median_bias_hpa'],1.0)
        self.assertAlmostEqual(m['mae_hpa'],2.0)

    def test_era5_ingest_fails_closed_on_manifest_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);payload=json.dumps({'elevation':480,'hourly':{'time':['2019-01-01T00:00'],'pressure_msl':[1000.0],'surface_pressure':[950.0],'temperature_2m':[4.0]}}).encode()
            (d/'loucka_era5_nearest-2019.json').write_bytes(payload)
            manifest={'points':{'loucka_era5_nearest':{}},'responses':[{'file':'loucka_era5_nearest-2019.json','sha256':hashlib.sha256(payload).hexdigest()}]}
            (d/'manifest.json').write_text(json.dumps(manifest))
            data,elev,_=load_era5(d)
            self.assertEqual(elev['loucka_era5_nearest'],480.0)
            self.assertEqual(next(iter(data['loucka_era5_nearest'].values())),(1000.0,950.0,4.0))
            manifest['responses'][0]['sha256']='0'*64;(d/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):load_era5(d)

    def test_combine_rejects_qc_rows_prefers_hourly_and_protects_q1_2018(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);v1=d/'v1.csv';era=d/'era.csv';qc=d/'qc.csv'
            fields=['dateTime_utc','original_value','estimated_value_hpa','reference_hourly_p95_max_hpa','local_holdout_p95_hpa','source','source_barometer_hpa','source_outTemp_c','model_sha256','reference_manifest_sha256']
            with v1.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([
                    {'dateTime_utc':1550000000,'original_value':'','estimated_value_hpa':'990','reference_hourly_p95_max_hpa':'1','local_holdout_p95_hpa':'1.2','source':'local','source_barometer_hpa':'1000','source_outTemp_c':'5','model_sha256':'m','reference_manifest_sha256':'r'},
                    {'dateTime_utc':1550000300,'original_value':'','estimated_value_hpa':'991','reference_hourly_p95_max_hpa':'1','local_holdout_p95_hpa':'1.2','source':'local','source_barometer_hpa':'1004','source_outTemp_c':'5','model_sha256':'m','reference_manifest_sha256':'r'},
                    {'dateTime_utc':Q1_START+10,'original_value':'','estimated_value_hpa':'992','reference_hourly_p95_max_hpa':'1','local_holdout_p95_hpa':'1.2','source':'local','source_barometer_hpa':'1000','source_outTemp_c':'5','model_sha256':'m','reference_manifest_sha256':'r'}])
            with era.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['dateTime_utc','estimated_value_hpa','method','reference_manifest_sha256','era5_manifest_sha256']);w.writeheader();w.writerow({'dateTime_utc':1550000000,'estimated_value_hpa':'989','method':'era5_surface','reference_manifest_sha256':'r','era5_manifest_sha256':'e'})
            with qc.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['dateTime_utc']);w.writeheader();w.writerow({'dateTime_utc':1550000300})
            report={'test_monthly':{'2019-02':{'models':{'era5_surface':{'gate':'PASS_DIAGNOSTIC_PREVIEW_ONLY','scores':{'H':{'p95_abs_error_hpa':1.1},'M':{'p95_abs_error_hpa':1.3}}}}}}}
            validation=d/'v.json';validation.write_text(json.dumps(report))
            rows,fields=combine(v1,era,qc,report);by={r['dateTime_utc']:r for r in rows}
            self.assertEqual(by[1550000000]['method'],'era5_surface')
            self.assertEqual(by[1550000300]['classification'],'UNRESOLVED')
            self.assertEqual(by[Q1_START+10]['dateTime_utc'] if Q1_START+10 in by else None,None)
            self.assertTrue(all(not Q1_START<=r['dateTime_utc']<Q1_END for r in rows))


if __name__=='__main__':unittest.main()
