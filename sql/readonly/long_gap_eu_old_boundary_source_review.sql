-- READ-ONLY SELECT; database_name=loucka_reconstruction; exact off-grid source keys and nearest existing reconstruction endpoints.
SELECT 'loucka_reconstruction' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM `loucka_reconstruction`.archive a WHERE a.dateTime IN (1248436740,1312296840,1330593780,1355404980,1437560459,1451091361,1454764141,1469553181,1512562620)
UNION ALL
SELECT 'pocasi-loucka.eu' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM `pocasi-loucka.eu`.archive a WHERE a.dateTime IN (1248436740,1312296840,1330593780,1355404980,1437560459,1451091361,1454764141,1469553181,1512562620)
UNION ALL
SELECT 'pocasi-loucka.eu_GW1000' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM `pocasi-loucka.eu_GW1000`.archive a WHERE a.dateTime IN (1248436740,1312296840,1330593780,1355404980,1437560459,1451091361,1454764141,1469553181,1512562620)
UNION ALL
SELECT 'pocasi-loucka.eu_old' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM `pocasi-loucka.eu_old`.archive a WHERE a.dateTime IN (1248436740,1312296840,1330593780,1355404980,1437560459,1451091361,1454764141,1469553181,1512562620)
UNION ALL
SELECT 'old_weewx' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM `old_weewx`.archive a WHERE a.dateTime IN (1248436740,1312296840,1330593780,1355404980,1437560459,1451091361,1454764141,1469553181,1512562620)
UNION ALL
SELECT 'weewx_WH1080' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM `weewx_WH1080`.archive a WHERE a.dateTime IN (1248436740,1312296840,1330593780,1355404980,1437560459,1451091361,1454764141,1469553181,1512562620)
UNION ALL
SELECT 'reconstruction_nearest_endpoint' AS source_database,a.`dateTime`,a.`usUnits`,a.`interval`,a.`outTemp`,a.`outHumidity`,a.`rain`,a.`rainRate`,a.`windSpeed`,a.`windDir`,a.`windGust`,a.`barometer` FROM archive a WHERE a.dateTime IN (1248436800,1312296900,1330593900,1355405100,1437560400,1451091300,1454764200,1469553300,1512562500);
