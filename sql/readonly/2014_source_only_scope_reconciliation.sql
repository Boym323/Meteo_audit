-- READ-ONLY reconciliation of EU-old-target field matrix vs reconstruction-target cohort; UTC 2014.
SELECT (r.dateTime IS NOT NULL) AS has_reconstruction, COUNT(*) AS n
FROM old_weewx.archive a
JOIN weewx_WH1080.archive b USING(dateTime)
LEFT JOIN `pocasi-loucka.eu_old`.archive z USING(dateTime)
LEFT JOIN loucka_reconstruction.archive r USING(dateTime)
WHERE a.dateTime>=1388534400 AND a.dateTime<1420070400 AND z.dateTime IS NULL
GROUP BY (r.dateTime IS NOT NULL);

-- Aggregate totals used to verify the keyspace and EU-old absence count.
SELECT (SELECT COUNT(*) FROM old_weewx.archive a WHERE dateTime>=1388534400 AND dateTime<1420070400) old_rows,
       (SELECT COUNT(*) FROM weewx_WH1080.archive b WHERE dateTime>=1388534400 AND dateTime<1420070400) wh_rows,
       (SELECT COUNT(*) FROM old_weewx.archive a JOIN weewx_WH1080.archive b USING(dateTime) WHERE a.dateTime>=1388534400 AND a.dateTime<1420070400) shared_rows,
       (SELECT COUNT(*) FROM `pocasi-loucka.eu_old`.archive z WHERE dateTime>=1388534400 AND dateTime<1420070400) eu_old_rows,
       (SELECT COUNT(*) FROM old_weewx.archive a JOIN weewx_WH1080.archive b USING(dateTime) LEFT JOIN `pocasi-loucka.eu_old`.archive z USING(dateTime) WHERE a.dateTime>=1388534400 AND a.dateTime<1420070400 AND z.dateTime IS NULL) shared_absent_eu_old;
