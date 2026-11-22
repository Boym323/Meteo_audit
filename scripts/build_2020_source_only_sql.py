#!/usr/bin/env python3
"""Generate reproducible read-only SQL for the 2020 source-only screen."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
fields=['barometer','pressure','altimeter','inTemp','outTemp','inHumidity','outHumidity','windSpeed','windDir','windGust','windGustDir','rainRate','rain','dewpoint','windchill','heatindex','ET','radiation','UV','extraTemp1','extraTemp2','extraTemp3','extraTemp4','soilTemp1','soilTemp2','soilTemp3','soilTemp4','leafTemp1','leafTemp2','extraHumid1','extraHumid2','soilMoist1','soilMoist2','soilMoist3','soilMoist4','leafWet1','leafWet2','rxCheckPercent','txBatteryStatus','consBatteryVoltage','hail','hailRate','heatingTemp','heatingVoltage','supplyVoltage','referenceVoltage','windBatteryStatus','rainBatteryStatus','outTempBatteryStatus','inTempBatteryStatus']
sel=['MONTH(FROM_UNIXTIME(a0.dateTime)) AS month_utc','COUNT(*) AS source_only_rows','SUM(MOD(a0.dateTime,300)<>0) AS off_grid_rows']
for f in fields:
    sel += [f'SUM(a0.`{f}` IS NOT NULL) AS `{f}_old_nonnull`',f'SUM(a1.`{f}` IS NOT NULL) AS `{f}_wh_nonnull`',f'SUM(a0.`{f}` IS NOT NULL AND a1.`{f}` IS NOT NULL AND a0.`{f}`=a1.`{f}`) AS `{f}_both_equal`',f'SUM(a0.`{f}` IS NOT NULL AND a1.`{f}` IS NOT NULL AND a0.`{f}`<>a1.`{f}`) AS `{f}_both_conflict`']
query='''-- READ-ONLY all-50-field monthly aggregate for exact source-copy timestamps absent from reconstruction.
SELECT\n  '''+',\n  '.join(sel)+'''\nFROM old_weewx.archive a0 JOIN weewx_WH1080.archive a1 ON a1.dateTime=a0.dateTime
LEFT JOIN loucka_reconstruction.archive a2 ON a2.dateTime=a0.dateTime
WHERE a0.dateTime>=1577836800 AND a0.dateTime<1609459200 AND a2.dateTime IS NULL
GROUP BY MONTH(FROM_UNIXTIME(a0.dateTime)) ORDER BY month_utc;\n'''
(R/'sql/readonly/2020_source_only_monthly_field_availability.sql').write_text(query)
