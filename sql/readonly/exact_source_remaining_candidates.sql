-- Read-only inventory for the scoped candidate years. Timestamp bounds are
-- explicit UTC epoch ranges; convert dateTime to ISO UTC in the local exporter.
-- Target value is NULL by the candidate predicate. Old WeeWX copies are
-- supplementary and are not treated as independent observations.
SELECT * FROM (
  SELECT t.dateTime, 'outTemp' AS variable, t.outTemp AS target_value,
         p.outTemp AS live_value, o.outTemp AS old_value, g.outTemp AS gw_value,
         p.usUnits AS live_units, p.interval AS live_interval,
         o.usUnits AS old_units, o.interval AS old_interval,
         g.usUnits AS gw_units, g.interval AS gw_interval,
         w.outTemp AS old_weewx_value, w.usUnits AS old_weewx_units, w.interval AS old_weewx_interval,
         h.outTemp AS wh1080_value, h.usUnits AS wh1080_units, h.interval AS wh1080_interval,
         t.outHumidity AS same_row_context
  FROM loucka_reconstruction.archive t
  LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=t.dateTime
  LEFT JOIN `pocasi-loucka.eu_old`.archive o ON o.dateTime=t.dateTime
  LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=t.dateTime
  LEFT JOIN old_weewx.archive w ON w.dateTime=t.dateTime
  LEFT JOIN weewx_WH1080.archive h ON h.dateTime=t.dateTime
  WHERE t.outTemp IS NULL AND (p.outTemp IS NOT NULL OR o.outTemp IS NOT NULL OR g.outTemp IS NOT NULL)
    AND ((t.dateTime>=1356998400 AND t.dateTime<1388534400)
      OR (t.dateTime>=1451606400 AND t.dateTime<1514764800)
      OR (t.dateTime>=1546300800 AND t.dateTime<1609459200)
      OR (t.dateTime>=1640995200 AND t.dateTime<1672531200))
  UNION ALL
  SELECT t.dateTime, 'outHumidity', t.outHumidity,
         p.outHumidity, o.outHumidity, g.outHumidity,
         p.usUnits, p.interval, o.usUnits, o.interval, g.usUnits, g.interval,
         w.outHumidity, w.usUnits, w.interval, h.outHumidity, h.usUnits, h.interval,
         t.outTemp
  FROM loucka_reconstruction.archive t
  LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=t.dateTime
  LEFT JOIN `pocasi-loucka.eu_old`.archive o ON o.dateTime=t.dateTime
  LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=t.dateTime
  LEFT JOIN old_weewx.archive w ON w.dateTime=t.dateTime
  LEFT JOIN weewx_WH1080.archive h ON h.dateTime=t.dateTime
  WHERE t.outHumidity IS NULL AND (p.outHumidity IS NOT NULL OR o.outHumidity IS NOT NULL OR g.outHumidity IS NOT NULL)
    AND ((t.dateTime>=1356998400 AND t.dateTime<1388534400)
      OR (t.dateTime>=1451606400 AND t.dateTime<1514764800)
      OR (t.dateTime>=1546300800 AND t.dateTime<1609459200)
      OR (t.dateTime>=1640995200 AND t.dateTime<1672531200))
) remaining_candidates
ORDER BY dateTime, variable;
