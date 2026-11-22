import unittest

from build_authoritative_statistical_readiness import classify


class ValueLevelProvenanceTests(unittest.TestCase):
    def test_timestamp_membership_does_not_classify_other_values(self):
        audit = {100: {"outTemp": "12.5", "outHumidity": "60"}}
        self.assertEqual(classify(100, "outTemp", 12.5, audit, {}, {}), "RECOVERED_SOURCE")
        self.assertEqual(classify(100, "windSpeed", 3.2, audit, {}, {}), "UNCLASSIFIED")
        self.assertEqual(classify(100, "outTemp", 12.6, audit, {}, {}), "UNCLASSIFIED")

    def test_later_applied_change_takes_precedence(self):
        audit = {100: {"outTemp": "12.5"}}
        changes = {(100, "outTemp"): {"new_value": "12.6", "class": "CORRECTED"}}
        self.assertEqual(classify(100, "outTemp", 12.6, audit, {}, changes), "CORRECTED")

    def test_applied_estimate_is_not_source(self):
        audit = {100: {"outTemp": "12.5"}}
        self.assertEqual(classify(100, "outTemp", 12.5, audit, {(100, "outTemp"): "12.5"}, {}), "ESTIMATED")


if __name__ == "__main__":
    unittest.main()
