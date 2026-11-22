import unittest

from meteo_audit.readiness_snapshot_adapter import readiness_category


class ReadinessSnapshotCategoryTests(unittest.TestCase):
    def test_strict_categories_are_retained(self):
        for category in ("RECOVERED_SOURCE", "RESTORED", "CORRECTED", "ESTIMATED"):
            with self.subTest(category=category):
                self.assertEqual(readiness_category(category), category)

    def test_archive_copy_agreement_does_not_become_verified_lineage(self):
        for category in ("SOURCE_MATCHED", "CONFLICTING_SOURCE", "UNCLASSIFIED", "UNRESOLVED", "INVALIDATED"):
            with self.subTest(category=category):
                self.assertEqual(readiness_category(category), "UNCLASSIFIED")


if __name__ == "__main__":
    unittest.main()
