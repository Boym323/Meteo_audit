import unittest

from meteo_audit.lightning_qc import LightningEvidenceError, inspect_lightning_evidence


def summary(source, *, target_n=3, matched_rows=3, disturber_nonnull=2,
            disturber_exact_matches=1, noise_nonnull=2, noise_equals_strike=2):
    return {
        "source": source,
        "target_n": str(target_n),
        "matched_rows": str(matched_rows),
        "disturber_nonnull": str(disturber_nonnull),
        "disturber_exact_matches": str(disturber_exact_matches),
        "noise_nonnull": str(noise_nonnull),
        "noise_equals_strike": str(noise_equals_strike),
    }


class LightningEvidenceTests(unittest.TestCase):
    def test_returns_only_aggregate_mapping_diagnostics(self):
        result = inspect_lightning_evidence(
            [summary("target"), summary("reference", target_n=3, matched_rows=2,
                                       disturber_nonnull=0, disturber_exact_matches=0,
                                       noise_nonnull=0, noise_equals_strike=0)],
            [
                {"dateTime": "1700000000", "lightning_disturber_count": "1700000001",
                 "lightning_strike_count": "0", "lightning_noise_count": "0"},
                {"dateTime": "1700000300", "lightning_disturber_count": "7",
                 "lightning_strike_count": "2", "lightning_noise_count": "2"},
            ],
            target_source="target",
        )
        self.assertEqual(result["target_rows"], 3)
        self.assertEqual(result["disturber_exceeds_epoch_count"], 1)
        self.assertEqual(result["noise_equals_strike_count"], 2)
        self.assertEqual(result["interpretation"], "diagnostic_only_mapping_semantics_unverified")
        self.assertNotIn("source", result)
        self.assertNotIn("dateTime", result)

    def test_rejects_duplicate_source_labels(self):
        with self.assertRaisesRegex(LightningEvidenceError, "unique"):
            inspect_lightning_evidence([summary("same"), summary("same")], [], target_source="same")

    def test_rejects_inconsistent_counts(self):
        bad = summary("target", matched_rows=4)
        with self.assertRaisesRegex(LightningEvidenceError, "matched_rows"):
            inspect_lightning_evidence([bad], [], target_source="target")

    def test_rejects_negative_or_noninteger_sample_values(self):
        examples = [{"dateTime": "10", "lightning_disturber_count": "NaN",
                     "lightning_strike_count": "0", "lightning_noise_count": "0"}]
        with self.assertRaisesRegex(LightningEvidenceError, "non-negative integer"):
            inspect_lightning_evidence([summary("target")], examples, target_source="target")

    def test_accepts_null_sensor_fields_without_treating_them_as_zero(self):
        examples = [{"dateTime": "10", "lightning_disturber_count": "\\N",
                     "lightning_strike_count": "NULL", "lightning_noise_count": ""}]
        result = inspect_lightning_evidence([summary("target")], examples, target_source="target")
        self.assertEqual(result["samples_with_disturber"], 0)
        self.assertEqual(result["noise_equals_strike_count"], 0)


if __name__ == "__main__":
    unittest.main()
