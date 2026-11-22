-- READ-ONLY timestamp evidence; fixed UTC 2016; compare labels locally.
SELECT 'old_weewx' AS source_name, `dateTime` FROM `old_weewx`.`archive` WHERE `dateTime`>=1451606400 AND `dateTime`<1483228800
UNION ALL
SELECT 'weewx_WH1080', `dateTime` FROM `weewx_WH1080`.`archive` WHERE `dateTime`>=1451606400 AND `dateTime`<1483228800
UNION ALL
SELECT 'pocasi-loucka.eu_old', `dateTime` FROM `pocasi-loucka.eu_old`.`archive` WHERE `dateTime`>=1451606400 AND `dateTime`<1483228800;
