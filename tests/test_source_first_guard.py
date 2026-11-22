import unittest
from meteo_audit.source_first import classify_before_estimate, restored_gate, validate_dependency_order

class SourceFirstGuardTests(unittest.TestCase):
    def classify(self, **kw):
        defaults=dict(source_checks_complete=True,sources=[{"source_row_exists":False,"value":None}],target_row_exists=False,change_event_count=0)
        defaults.update(kw)
        return classify_before_estimate(**defaults)

    def test_exact_source_value_blocks_estimated(self):
        d=self.classify(sources=[{"source_row_exists":True,"value":18.2}])
        self.assertEqual(d.status,"REVIEW_REQUIRED")
        self.assertIn("RESTORED/source conflict",d.reason)

    def test_whole_source_row_without_variable_still_blocks_insert(self):
        d=self.classify(sources=[{"source_row_exists":True,"value":None}])
        self.assertEqual(d.status,"REVIEW_REQUIRED")
        self.assertIn("multi-variable",d.reason)

    def test_incomplete_sources_block_estimate(self):
        self.assertEqual(self.classify(source_checks_complete=False).status,"REVIEW_REQUIRED")

    def test_missing_exact_row_and_no_history_can_reach_model_gate(self):
        self.assertEqual(self.classify().status,"ESTIMATED_ELIGIBLE_FOR_REVIEW")

    def test_change_event_blocks_estimate(self):
        self.assertEqual(self.classify(change_event_count=1).status,"REVIEW_REQUIRED")

    def test_restored_requires_every_provenance_gate(self):
        gates=dict(original_identity=True,source_role_verified=True,timestamp_verified=True,unit_verified=True,
                   expected_target_state_verified=True,history_checked=True,context_checked=True,
                   anomaly_screen_passed=True,uncertainty_documented=True,
                   historical_transformation_resolved=True,historical_removal_screen_passed=True)
        self.assertEqual(restored_gate(**gates).status,"RESTORED_ELIGIBLE_FOR_REVIEW")
        gates['source_role_verified']=False
        self.assertEqual(restored_gate(**gates).status,"REVIEW_REQUIRED")

    def test_whole_row_insert_precedes_field_fills(self):
        valid=[{"operation":"insert_row","timestamp":100,"variable":"__row__"},
               {"operation":"set_field","timestamp":100,"variable":"outTemp","expected_row_state":"ABSENT"}]
        validate_dependency_order(valid)
        with self.assertRaises(ValueError):
            validate_dependency_order(list(reversed(valid)))

if __name__=='__main__': unittest.main()
