"""Offline checks for the CHMI reference downloader."""
import importlib.util
import json
import unittest
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


if __name__ == "__main__":
    unittest.main()
