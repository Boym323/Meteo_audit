"""Check aggregate range-screen counts recorded in the secondary-channel report."""
from csv import DictReader
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "reports/2026-11-13-secondary-channel-followup.csv"
rows = {row["variable"]: row for row in DictReader(path.open(newline="", encoding="utf-8"))}
expected = {
    "inTemp": (433955, "0"), "inHumidity": (433983, "0"),
    "extraTemp1": (417334, "2"), "extraTemp2": (90145, "790"),
    "extraHumid1": (0, "0"), "extraHumid2": (0, "0"),
    "soilTemp1": (689061, "1"), "soilTemp2": (379865, "0"),
    "soilTemp3": (691881, "0"), "soilTemp4": (679120, "0"),
    "soilTemp5": (688931, "10"), "soilTemp6": (679494, "21"),
    "soilMoist1": (387955, "0"), "soilad1": (67746, "0"),
}
assert set(rows) == set(expected)
for key, (count, outside) in expected.items():
    assert int(rows[key]["nonnull"]) == count, key
    assert rows[key]["outside_count"] == outside, key
assert sum(int(rows[f"soilTemp{i}"]["outside_count"]) for i in (1, 5, 6)) == 32
assert int(rows["extraTemp2"]["nonnull"]) > int(rows["extraTemp2"]["outside_count"])
print("secondary channel aggregate checks: OK (14 channels)")
