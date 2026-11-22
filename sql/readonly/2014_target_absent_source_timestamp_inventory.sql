-- READ-ONLY timestamp inventory; fixed UTC 2014.
SELECT 'old_weewx' AS source_name, `dateTime` FROM `old_weewx`.`archive` WHERE `dateTime`>=1388534400 AND `dateTime`<1420070400
UNION ALL SELECT 'weewx_WH1080', `dateTime` FROM `weewx_WH1080`.`archive` WHERE `dateTime`>=1388534400 AND `dateTime`<1420070400
UNION ALL SELECT 'pocasi-loucka.eu_old', `dateTime` FROM `pocasi-loucka.eu_old`.`archive` WHERE `dateTime`>=1388534400 AND `dateTime`<1420070400;
