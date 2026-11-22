import unittest
from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/inspect_lightning_mapper_readonly.py"
spec = importlib.util.spec_from_file_location("lightning_mapper_readonly", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SanitizedLightningMapperTests(unittest.TestCase):
    def test_finds_suspicious_timestamp_and_strike_alias_without_declaring_truth(self):
        report = module.inspect_configuration("""
        [[field_map_extensions]]
        lightning_disturber_count = lightning_time
        lightning_noise_count = lightning_strike_count
        lightning_strike_count = lightning_num
        """)
        self.assertEqual(len(report["mapping_candidates"]), 3)
        self.assertEqual(report["mapping_candidates"][0]["status"],
                         "POSSIBLE_TIMESTAMP_IN_DISTURBER")
        self.assertEqual(report["mapping_candidates"][1]["status"],
                         "POSSIBLE_STRIKE_ALIAS_IN_NOISE")
        self.assertEqual(report["mapping_candidates"][2]["status"],
                         "UNVERIFIED_FIELD_SEMANTICS")
        self.assertFalse(report["driver_and_raw_payload_verified"])
        self.assertFalse(report["historical_db_update_authorized"])

    def test_never_emits_config_secrets_or_unknown_text(self):
        hidden = "1234567890-PRIVATE-ECOWITT-SECRET"
        text = (
            "[Station]\npassword = "+hidden+
            "\nlightning_noise_count = "+hidden+
            "\nlightning_disturber_count = lightning_last_det_time"
            "\nstation_api_key = "+hidden+
            "\n"
        )
        report = module.inspect_configuration(text)
        serialized = str(report)
        self.assertNotIn(hidden, serialized)
        self.assertNotIn("password", serialized)
        self.assertNotIn("station_api_key", serialized)
        self.assertIsNone(report["mapping_candidates"][0]["mapped_allowlisted_key"])

    def test_driver_scan_reports_only_allowlisted_names_and_counts(self):
        report = module.inspect_driver_presence(
            "password=my-secret\nlightning_time lightning_time lightning_num"
            "\nlightning_disturber_count"
        )
        self.assertEqual(report["lightning_time"], 2)
        self.assertEqual(report["lightning_num"], 1)
        self.assertEqual(report["lightning_disturber_count"], 1)
        self.assertNotIn("password", report)
        self.assertNotIn("my-secret", str(report))

    def test_null_or_unknown_config_cannot_fabricate_mapper_evidence(self):
        result = module.inspect_configuration("field_map = nothing\npassword=abc\n")
        self.assertEqual(result["mapping_candidates"], [])
        self.assertFalse(result["driver_and_raw_payload_verified"])

    def test_disallows_unbounded_rhs_display(self):
        result = module.inspect_configuration(
            "lightning_noise_count = something.incidental;token=sensitive"
        )
        self.assertEqual(len(result["mapping_candidates"]), 1)
        self.assertIsNone(result["mapping_candidates"][0]["mapped_allowlisted_key"])


if __name__ == "__main__":
    unittest.main()
