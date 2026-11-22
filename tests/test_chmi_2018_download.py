"""Offline checks for the CHMI reference downloader."""
import importlib.util
import json
import unittest
import tempfile
from unittest.mock import patch
from urllib.error import HTTPError
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "chmi_2018_download", Path(__file__).resolve().parents[1] / "scripts" / "chmi_2018_download.py")
chmi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chmi)
STATION = chmi.STATIONS[0]


def sample(values):
    return json.dumps({"data": {"data": {"header": "STATION,ELEMENT,DT,VAL,FLAG,QUALITY",
                                       "values": values}}}).encode()


class DownloadParserTests(unittest.TestCase):
    def test_preserves_zero_and_quality(self):
        rows, issues = chmi.parse(sample([
            [STATION, "T", "2018-01-01T00:00:00Z", 0, "", 0],
            [STATION, "H", "2018-01-01T00:00:00Z", 85, "X", 1],
            [STATION, "H", "2018-01-01T00:10:00Z", 101, "", 0],
        ]), STATION, 2018, 1)
        self.assertEqual(rows[(1514764800, "T")], (0, "", 0, True))
        self.assertEqual(rows[(1514764800, "H")], (85, "X", 1, True))
        self.assertFalse(rows[(1514765400, "H")][3])
        self.assertEqual(issues["H_flag_or_quality_nonzero"], 1)
        self.assertEqual(issues["H_invalid_or_missing"], 1)

    def test_rejects_duplicates(self):
        row = [STATION, "T", "2018-01-01T00:00:00Z", 1, "", 0]
        with self.assertRaises(ValueError):
            chmi.parse(sample([row, row]), STATION, 2018, 1)

    def test_rejects_wrong_month_station_and_grid(self):
        for station, stamp in [(STATION, "2018-02-01T00:00:00Z"),
                               (STATION, "2018-01-01T00:05:00Z"),
                               (STATION, "2018-01-01T00:00:00+01:00"),
                               (chmi.STATIONS[1], "2018-01-01T00:00:00Z")]:
            with self.subTest(station=station, stamp=stamp):
                with self.assertRaises(ValueError):
                    chmi.parse(sample([[station, "T", stamp, 1, "", 0]]), STATION, 2018, 1)

    def test_missing_element_reported(self):
        _, issues = chmi.parse(sample([
            [STATION, "T", "2018-01-01T00:00:00Z", 1, "", 0]
        ]), STATION, 2018, 1)
        self.assertEqual(issues["H_absent"], 1)

    def test_optional_boundary_404_does_not_block_2018(self):
        def fake_read(path, url, station, year, month):
            if year == 2017:
                raise HTTPError(url, 404, "Not Found", {}, None)
            return b"{}", {}, chmi.Counter()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(chmi, "read_file", side_effect=fake_read) as read, \
                 patch("sys.argv", ["download", "--out", tmp, "--include-boundary"]):
                chmi.main()
            manifest = json.loads((root / "manifest.json").read_text())
            self.assertEqual(read.call_count, 26)
            self.assertEqual(len(manifest), 26)
            self.assertEqual(sum(r["status"] == "downloaded" for r in manifest), 24)
            missing = [r for r in manifest if r["status"] == "unavailable_http_404"]
            self.assertEqual(len(missing), 2)
            self.assertTrue(all(r["month"] == "201712" and r["sha256"] is None
                                and r["paired"] == 0 for r in missing))
            self.assertTrue((root / "reference_TH.csv").exists())

    def test_required_2018_404_is_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chmi, "read_file", side_effect=HTTPError(
                    "https://example.invalid", 404, "Not Found", {}, None)), \
                 patch("sys.argv", ["download", "--out", tmp]):
                with self.assertRaises(HTTPError):
                    chmi.main()
            self.assertFalse((Path(tmp) / "manifest.json").exists())

    def test_read_file_does_not_retry_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(chmi, "urlopen", side_effect=HTTPError(
                    "https://example.invalid", 404, "Not Found", {}, None)) as request:
                with self.assertRaises(HTTPError):
                    chmi.read_file(Path(tmp) / "raw.json", "https://example.invalid",
                                   STATION, 2017, 12)
                self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
