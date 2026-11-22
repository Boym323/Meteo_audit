-- SELECT-only unit-code distributions. Run each statement separately.
-- `usUnits` is reported as stored; no unit conversion occurs.
SELECT usUnits,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `loucka_reconstruction`.`archive` GROUP BY usUnits ORDER BY usUnits;
SELECT usUnits,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `old_weewx`.`archive` GROUP BY usUnits ORDER BY usUnits;
SELECT usUnits,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `weewx_WH1080`.`archive` GROUP BY usUnits ORDER BY usUnits;
SELECT usUnits,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu`.`archive` GROUP BY usUnits ORDER BY usUnits;
SELECT usUnits,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu_GW1000`.`archive` GROUP BY usUnits ORDER BY usUnits;
SELECT usUnits,COUNT(*) AS rows_n,MIN(dateTime) AS first_epoch,MAX(dateTime) AS last_epoch
FROM `pocasi-loucka.eu_old`.`archive` GROUP BY usUnits ORDER BY usUnits;
