import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "readonly_archive_extract.py"
spec = importlib.util.spec_from_file_location("readonly_archive_extract", SCRIPT)
extract = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(extract)


class ReadOnlyArchiveExtractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "extract.csv"

    def args(self, *args):
        return ["readonly_archive_extract.py", *args, "--output", str(self.out)]

    def test_bounded_allowlisted_readonly_select(self):
        captured = {}
        def fake_query(sql, *, env_file, timeout):
            captured.update(sql=sql, env_file=env_file, timeout=timeout)
            return ["1400000001\t17\t5\t18.2", "1400000002\t17\t5\t18.3"]
        with patch.object(extract, "query", fake_query), patch.object(sys, "argv", self.args(
            "--database", "old_weewx", "--start-utc", "1400000000",
            "--end-utc", "1400000300", "--fields", "dateTime,usUnits,interval,outTemp",
        )):
            self.assertEqual(extract.main(), 0)
        sql = captured["sql"]
        tick = chr(96)
        self.assertTrue(sql.startswith("SELECT "))
        self.assertIn("FROM " + tick + "old_weewx" + tick + "." + tick + "archive" + tick, sql)
        self.assertIn("dateTime" + tick + " > 1400000000", sql)
        self.assertIn("dateTime" + tick + " <= 1400000300", sql)
        self.assertIn("LIMIT 50000", sql)
        self.assertNotIn(";", sql)
        self.assertEqual(captured["timeout"], 600)
        self.assertEqual(self.out.read_text().splitlines(), [
            "dateTime,usUnits,interval,outTemp",
            "1400000001,17,5,18.2",
            "1400000002,17,5,18.3",
        ])

    def test_rejects_non_allowlisted_database_and_long_range(self):
        cases = [
            self.args("--database", "information_schema", "--start-utc", "1", "--end-utc", "2"),
            self.args("--database", "old_weewx", "--start-utc", "1",
                      "--end-utc", str(1 + extract.MAX_RANGE_SECONDS + 1)),
        ]
        for argv in cases:
            with self.subTest(argv=argv), patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as err:
                    extract.main()
                self.assertEqual(err.exception.code, 2)

    def test_refuses_existing_output_and_rejects_limit_saturation(self):
        self.out.write_text("keep")
        with patch.object(extract, "query") as query_mock, patch.object(sys, "argv", self.args(
            "--database", "old_weewx", "--start-utc", "1400000000", "--end-utc", "1400000300",
        )), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                extract.main()
        query_mock.assert_not_called()
        self.assertEqual(self.out.read_text(), "keep")

        self.out.unlink()
        with patch.object(extract, "query", return_value=["a\t1", "b\t2"]), patch.object(sys, "argv", self.args(
            "--database", "old_weewx", "--start-utc", "1400000000",
            "--end-utc", "1400000300", "--limit", "2", "--fields", "dateTime,outTemp",
        )):
            with self.assertRaisesRegex(RuntimeError, "row limit reached"):
                extract.main()
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
