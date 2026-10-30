import unittest
from meteo_audit.detector import RainPoint, Quality, screen_rain

class DetectorTests(unittest.TestCase):
    def test_missing_is_unresolved_not_zero(self):
        findings = screen_rain([RainPoint(1000, 5, None, 0.0)])
        self.assertEqual(findings[0].quality, Quality.UNRESOLVED)
        self.assertIsNone(findings[0].proposed_value)

    def test_extreme_with_zero_rate_is_candidate_only(self):
        findings = screen_rain([RainPoint(1000, 5, 30.72, 0.0)])
        self.assertEqual(findings[0].quality, Quality.SUSPECTED)
        self.assertIsNone(findings[0].proposed_value)

    def test_reasonable_point_not_flagged(self):
        self.assertEqual(screen_rain([RainPoint(1000, 5, 0.2, 2.4)]), [])

if __name__ == '__main__':
    unittest.main()
