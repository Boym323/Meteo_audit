-- READ-ONLY, bounded 2013 source-only cohort with exact agreement on the five
-- primary fields. Nearest 300-second projection is diagnostic, not a shift rule.
WITH c AS (
  SELECT o.dateTime AS source_time,
         CASE WHEN MOD(o.dateTime,300)<=150
              THEN o.dateTime-MOD(o.dateTime,300)
              ELSE o.dateTime+(300-MOD(o.dateTime,300)) END AS projected_time,
         o.usUnits,o.`interval`,o.outTemp,o.outHumidity,o.rain,o.rainRate,o.windSpeed,
         o.windGust,o.windDir,o.barometer
  FROM old_weewx.archive o
  JOIN weewx_WH1080.archive w ON w.dateTime=o.dateTime
  LEFT JOIN loucka_reconstruction.archive x ON x.dateTime=o.dateTime
  WHERE o.dateTime>=1356998400 AND o.dateTime<1388534400
    AND x.dateTime IS NULL AND o.usUnits=17 AND w.usUnits=17
    AND o.`interval`=5 AND w.`interval`=5
),
eligible AS (
  SELECT * FROM c
  WHERE outTemp IS NOT NULL AND outHumidity IS NOT NULL AND rain IS NOT NULL
    AND rainRate IS NOT NULL AND windSpeed IS NOT NULL
    AND EXISTS (SELECT 1 FROM old_weewx.archive o2 JOIN weewx_WH1080.archive w2
                ON w2.dateTime=o2.dateTime
                WHERE o2.dateTime=c.source_time
                  AND o2.outTemp<=>w2.outTemp AND o2.outHumidity<=>w2.outHumidity
                  AND o2.rain<=>w2.rain AND o2.rainRate<=>w2.rainRate
                  AND o2.windSpeed<=>w2.windSpeed)
    AND NOT EXISTS (SELECT 1 FROM loucka_reconstruction.archive t
                    WHERE t.dateTime=c.projected_time)
)
SELECT q.source_time,q.projected_time,q.source_time-q.projected_time AS offset_seconds,
       q.usUnits,q.`interval`,q.outTemp,q.outHumidity,q.rain,q.rainRate,q.windSpeed,
       q.windGust,q.windDir,q.barometer,
       r0.dateTime IS NOT NULL AS reconstruction_at_source,
       e0.dateTime IS NOT NULL AS eu_at_source,
       g0.dateTime IS NOT NULL AS gw1000_at_source,
       eo0.dateTime IS NOT NULL AS eu_old_at_source,
       o0.dateTime IS NOT NULL AS old_weewx_at_source,
       w0.dateTime IS NOT NULL AS wh1080_at_source,
       r1.dateTime IS NOT NULL AS reconstruction_at_projection,
       e1.dateTime IS NOT NULL AS eu_at_projection,
       g1.dateTime IS NOT NULL AS gw1000_at_projection,
       eo1.dateTime IS NOT NULL AS eu_old_at_projection,
       o1.dateTime IS NOT NULL AS old_weewx_at_projection,
       w1.dateTime IS NOT NULL AS wh1080_at_projection,
       ref.observed_at_utc IS NOT NULL AS luhamet_exact_at_source,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h
        WHERE h.target_time=q.source_time) AS source_change_events,
       (SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes h
        WHERE h.target_time=q.projected_time) AS projection_change_events
FROM eligible q
LEFT JOIN loucka_reconstruction.archive r0 ON r0.dateTime=q.source_time
LEFT JOIN `pocasi-loucka.eu`.archive e0 ON e0.dateTime=q.source_time
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g0 ON g0.dateTime=q.source_time
LEFT JOIN `pocasi-loucka.eu_old`.archive eo0 ON eo0.dateTime=q.source_time
LEFT JOIN old_weewx.archive o0 ON o0.dateTime=q.source_time
LEFT JOIN weewx_WH1080.archive w0 ON w0.dateTime=q.source_time
LEFT JOIN loucka_reconstruction.archive r1 ON r1.dateTime=q.projected_time
LEFT JOIN `pocasi-loucka.eu`.archive e1 ON e1.dateTime=q.projected_time
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g1 ON g1.dateTime=q.projected_time
LEFT JOIN `pocasi-loucka.eu_old`.archive eo1 ON eo1.dateTime=q.projected_time
LEFT JOIN old_weewx.archive o1 ON o1.dateTime=q.projected_time
LEFT JOIN weewx_WH1080.archive w1 ON w1.dateTime=q.projected_time
LEFT JOIN loucka_reconstruction.reference_observations ref
  ON ref.station_id='luhamet_sehradice' AND ref.observed_at_utc=q.source_time
ORDER BY q.source_time;
