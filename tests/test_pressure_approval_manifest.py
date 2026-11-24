import hashlib
import json
import unittest
from pathlib import Path


class PressureApprovalManifestTests(unittest.TestCase):
    def test_manifest_is_read_only_and_empty(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "proposals/pressure-approval-manifest-2026-11-24.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(doc["mode"], "READ_ONLY_NO_DATA_WRITE_AUTHORIZED")
        self.assertEqual(doc["candidate_count"], 0)
        self.assertEqual(doc["candidates"], [])
        self.assertIsNone(doc["batch_id"])
        self.assertFalse(doc["rollback"]["available"])
        self.assertEqual(doc["safety"]["database_mutations"], 0)
        recorded = (root / "proposals/pressure-approval-manifest-2026-11-24.json.sha256").read_text().split()[0]
        self.assertEqual(recorded, hashlib.sha256(path.read_bytes()).hexdigest())

    def test_candidate_hash_matches_canonical_empty_list(self):
        root = Path(__file__).resolve().parents[1]
        doc = json.loads((root / "proposals/pressure-approval-manifest-2026-11-24.json").read_text())
        canonical = json.dumps(doc["candidates"], ensure_ascii=False, separators=(",", ":")).encode()
        self.assertEqual(doc["sha256_candidates"], hashlib.sha256(canonical).hexdigest())


if __name__ == "__main__":
    unittest.main()
