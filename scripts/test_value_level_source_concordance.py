import unittest
from decimal import Decimal

from build_value_level_source_concordance import normalize


class UnitNormalizationTests(unittest.TestCase):
    def test_metricwx_wind_speed_is_converted_before_exact_comparison(self):
        self.assertEqual(normalize(Decimal("2.5"), "windSpeed", 17), Decimal("9.00"))

    def test_non_speed_metricwx_fields_are_unchanged(self):
        self.assertEqual(normalize(Decimal("12.3"), "outTemp", 17), Decimal("12.3"))
        self.assertEqual(normalize(Decimal("1013.2"), "pressure", 17), Decimal("1013.2"))

    def test_us_temperature_conversion_is_explicit(self):
        self.assertEqual(normalize(Decimal("68"), "outTemp", 1), Decimal(20))

    def test_unknown_unit_system_fails_closed(self):
        self.assertIsNone(normalize(5, "windSpeed", 99))


if __name__ == "__main__":
    unittest.main()
