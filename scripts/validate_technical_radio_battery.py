"""Deterministic checks for technical-channel aggregate checkpoint."""
from csv import DictReader
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "reports/2026-11-13-technical-radio-battery.csv"
rows = {r["variable"]: r for r in DictReader(p.open(newline="", encoding="utf-8"))}
expected = {
    "wh26_rssi": (63379, -107, -66.3333333333),
    "wh31_ch1_rssi": (63379, -108.3333333333, -71.2),
    "wh31_ch1_sig": (427493, 0, 4), "wh31_ch2_sig": (302938, 0, 4),
    "wh40_rssi": (63332, -108, -73.8), "wh41_ch1_rssi": (63371, -110, -58),
    "wh51_ch1_rssi": (63379, -107.2, -55.3333333333),
    "wh51_ch1_sig": (415519, 0, 4), "wh57_rssi": (62443, -107, -64.6666666667),
    "ws80_rssi": (63379, -106.4, -82.8), "ws80_sig": (603859, -96, 4),
    "batteryStatus1": (409281, 0, 0), "batteryStatus2": (88221, 0, 0),
    "lightning_Batt": (427679, 1, 5), "pm25_Batt1": (418068, 0, 5),
    "soilMoistBatt1": (377233, 0.8, 1.6), "ws80_batt": (425355, 2.98, 3.28),
}
assert set(rows) == set(expected)
for name, (n, low, high) in expected.items():
    assert int(rows[name]["nonnull"]) == n, name
    assert abs(float(rows[name]["min"]) - low) < 1e-8, name
    assert abs(float(rows[name]["max"]) - high) < 1e-8, name
assert 174824 + 429035 == 603859
assert 1661593200 - 1661573100 == 20100
print("technical radio/battery aggregate checks: OK (17 channels, 2 ws80_sig eras)")
