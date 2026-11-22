-- Diagnostic only: protected year 2021. No candidate or correction output.
-- UTC epoch bounds [2021-01-01, 2022-01-01); archive timestamps remain Unix UTC.
SELECT COUNT(*) AS rows_total,
       MIN(dateTime) AS min_epoch_utc,
       MAX(dateTime) AS max_epoch_utc,
       MIN(`interval`) AS min_interval_min,
       MAX(`interval`) AS max_interval_min,
       SUM(`interval` <> 5) AS non5_interval_rows,
       SUM(outTemp IS NULL) AS null_outTemp,
       MIN(outTemp) AS min_outTemp,
       MAX(outTemp) AS max_outTemp,
       SUM(outTemp < -40 OR outTemp > 60) AS outTemp_outside_wide_screen,
       SUM(outHumidity IS NULL) AS null_outHumidity,
       MIN(outHumidity) AS min_outHumidity,
       MAX(outHumidity) AS max_outHumidity,
       SUM(outHumidity < 0 OR outHumidity > 100) AS outHumidity_outside_range,
       SUM(rain IS NULL) AS null_rain,
       MIN(rain) AS min_rain,
       MAX(rain) AS max_rain,
       SUM(rain < 0) AS negative_rain,
       SUM(rainRate IS NULL) AS null_rainRate,
       MIN(rainRate) AS min_rainRate,
       MAX(rainRate) AS max_rainRate,
       SUM(rainRate < 0) AS negative_rainRate,
       SUM(barometer IS NULL) AS null_barometer,
       MIN(barometer) AS min_barometer,
       MAX(barometer) AS max_barometer,
       SUM(windSpeed IS NULL) AS null_windSpeed,
       MIN(windSpeed) AS min_windSpeed,
       MAX(windSpeed) AS max_windSpeed,
       SUM(windDir IS NULL) AS null_windDir,
       SUM(windSpeed > 0 AND windDir IS NULL) AS positive_wind_missing_dir,
       SUM(radiation IS NULL) AS null_radiation,
       SUM(uv IS NULL) AS null_uv,
       SUM(pm25_1 IS NULL) AS null_pm25_1,
       SUM(outTemp < 0) AS freezing_rows,
       MIN(CASE WHEN outTemp < 0 THEN outTemp END) AS minimum_freezing_temp,
       SUM(outTemp < -10) AS rows_below_minus10,
       SUM(outTemp < 0 AND windSpeed < 3) AS freezing_low_wind_rows,
       SUM(outTemp < 0 AND windSpeed IS NULL) AS freezing_wind_unknown,
       SUM(rain > 0 AND rainRate = 0) AS wet_rain_zero_rate,
       SUM(rain = 0 AND rainRate > 0) AS zero_rain_positive_rate,
       SUM(rain IS NULL AND rainRate > 0) AS null_rain_positive_rate,
       SUM(rain > 0 AND rainRate > 0) AS both_positive
FROM archive
WHERE dateTime >= 1609459200 AND dateTime < 1640995200;

-- Cadence and gap-size distribution. Conditional 5-minute slot arithmetic is
-- only a screen because no independent operational calendar is available.
SELECT COUNT(*) AS adjacent_pairs,
       SUM(delta_s = 300) AS delta_300s,
       SUM(delta_s <> 300) AS non300_pairs,
       SUM(delta_s > 300) AS gaps_gt_300s,
       MAX(delta_s) AS max_delta_s,
       SUM(delta_s > 600) AS gaps_gt_600s,
       SUM(delta_s >= 3600) AS gaps_ge_1h,
       SUM(delta_s >= 86400) AS gaps_ge_1d,
       SUM(GREATEST(FLOOR(delta_s / 300) - 1, 0)) AS conditional_5m_missing_slots,
       SUM(CASE WHEN delta_s > 300 AND MOD(delta_s, 300) = 0
                THEN FLOOR(delta_s / 300) - 1 ELSE 0 END) AS missing_slots_on_5m_grid
FROM (
    SELECT dateTime - LAG(dateTime) OVER (ORDER BY dateTime) AS delta_s
    FROM archive
    WHERE dateTime >= 1609459200 AND dateTime < 1640995200
) AS deltas
WHERE delta_s IS NOT NULL;
