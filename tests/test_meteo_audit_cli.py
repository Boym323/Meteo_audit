"""Safety and comparison tests for offline audit CLI."""
import argparse
import json
import tempfile
import unittest
from pathlib import Path
from scripts.meteo_audit import ROOT, run_validator, compare_manifests

class AuditCliTests(unittest.TestCase):
    def test_run_validator_rejects_run_root_outside_workspace(self):
        args=argparse.Namespace(script='scripts/validate_lightning_evidence.py', source=[], output=[], scope=[], name=None, run_root='../outside')
        with self.assertRaisesRegex(ValueError, 'run directory must stay inside'):
            run_validator(args)

    def test_compare_rejects_run_root_outside_workspace(self):
        args=argparse.Namespace(left='runs/a.json', right='runs/b.json', run_root='..', output='reports/diff.json')
        with self.assertRaisesRegex(ValueError, 'run directory must stay inside'):
            compare_manifests(args)

    def test_rejects_non_validator_script(self):
        args=argparse.Namespace(script='scripts/run_audit_checkpoint.py', source=[], output=[], scope=[], name=None, run_root='runs')
        with self.assertRaises(ValueError): run_validator(args)

    def test_compare_reports_hash_differences(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as td:
            d=Path(td); (d/'a.json').write_text(json.dumps({'run_id':'a','status':'succeeded','scope':{'analysis':'x'},'outputs':[{'path':'x.csv','sha256':'1'}]}))
            (d/'b.json').write_text(json.dumps({'run_id':'b','status':'succeeded','scope':{'analysis':'x'},'outputs':[{'path':'x.csv','sha256':'2'}]}))
            rel=lambda p:str(p.relative_to(ROOT))
            out=d/'diff.json'; args=argparse.Namespace(left=rel(d/'a.json'),right=rel(d/'b.json'),run_root=rel(ROOT/'runs'),output=rel(out))
            self.assertEqual(compare_manifests(args),0)
            self.assertEqual(json.loads(out.read_text())['changed_outputs'],['x.csv'])

    def test_compare_rejects_mismatched_scope(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as td:
            d=Path(td)
            for name,scope in [('a',{'year':'2019'}),('b',{'year':'2020'})]:
                (d/f'{name}.json').write_text(json.dumps({'run_id':name,'status':'succeeded','scope':scope,'outputs':[]}))
            rel=lambda p:str(p.relative_to(ROOT))
            args=argparse.Namespace(left=rel(d/'a.json'),right=rel(d/'b.json'),run_root=rel(ROOT/'runs'),output=rel(d/'diff.json'))
            with self.assertRaises(ValueError): compare_manifests(args)

if __name__=='__main__': unittest.main()
