-- READ-ONLY exact-time source/merged concordance, UTC 2011; does not establish lineage or correctness.
SELECT 2011 AS utc_year, COUNT(*) AS source_timestamp_pairs
  , SUM(o.`outTemp` IS NOT NULL) AS `outTemp__old_nonnull`
  , SUM(w.`outTemp` IS NOT NULL) AS `outTemp__wh_nonnull`
  , SUM((o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`=w.`outTemp`)) AS `outTemp__source_equal`
  , SUM((o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`<>w.`outTemp`)) AS `outTemp__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`outTemp` IS NOT NULL)) AS `outTemp__merged_nonnull`
  , SUM((m.`outTemp` IS NOT NULL AND o.`outTemp` IS NOT NULL AND m.`outTemp`=o.`outTemp`)) AS `outTemp__merged_matches_old`
  , SUM((m.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND m.`outTemp`=w.`outTemp`)) AS `outTemp__merged_matches_wh`
  , SUM((m.`outTemp` IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND m.`outTemp`<>o.`outTemp` AND m.`outTemp`<>w.`outTemp`)) AS `outTemp__merged_matches_neither`
  , SUM(o.`outHumidity` IS NOT NULL) AS `outHumidity__old_nonnull`
  , SUM(w.`outHumidity` IS NOT NULL) AS `outHumidity__wh_nonnull`
  , SUM((o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`=w.`outHumidity`)) AS `outHumidity__source_equal`
  , SUM((o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`<>w.`outHumidity`)) AS `outHumidity__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`outHumidity` IS NOT NULL)) AS `outHumidity__merged_nonnull`
  , SUM((m.`outHumidity` IS NOT NULL AND o.`outHumidity` IS NOT NULL AND m.`outHumidity`=o.`outHumidity`)) AS `outHumidity__merged_matches_old`
  , SUM((m.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND m.`outHumidity`=w.`outHumidity`)) AS `outHumidity__merged_matches_wh`
  , SUM((m.`outHumidity` IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND m.`outHumidity`<>o.`outHumidity` AND m.`outHumidity`<>w.`outHumidity`)) AS `outHumidity__merged_matches_neither`
  , SUM(o.`rain` IS NOT NULL) AS `rain__old_nonnull`
  , SUM(w.`rain` IS NOT NULL) AS `rain__wh_nonnull`
  , SUM((o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`=w.`rain`)) AS `rain__source_equal`
  , SUM((o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`<>w.`rain`)) AS `rain__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`rain` IS NOT NULL)) AS `rain__merged_nonnull`
  , SUM((m.`rain` IS NOT NULL AND o.`rain` IS NOT NULL AND m.`rain`=o.`rain`)) AS `rain__merged_matches_old`
  , SUM((m.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND m.`rain`=w.`rain`)) AS `rain__merged_matches_wh`
  , SUM((m.`rain` IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND m.`rain`<>o.`rain` AND m.`rain`<>w.`rain`)) AS `rain__merged_matches_neither`
  , SUM(o.`rainRate` IS NOT NULL) AS `rainRate__old_nonnull`
  , SUM(w.`rainRate` IS NOT NULL) AS `rainRate__wh_nonnull`
  , SUM((o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`=w.`rainRate`)) AS `rainRate__source_equal`
  , SUM((o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`<>w.`rainRate`)) AS `rainRate__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`rainRate` IS NOT NULL)) AS `rainRate__merged_nonnull`
  , SUM((m.`rainRate` IS NOT NULL AND o.`rainRate` IS NOT NULL AND m.`rainRate`=o.`rainRate`)) AS `rainRate__merged_matches_old`
  , SUM((m.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND m.`rainRate`=w.`rainRate`)) AS `rainRate__merged_matches_wh`
  , SUM((m.`rainRate` IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND m.`rainRate`<>o.`rainRate` AND m.`rainRate`<>w.`rainRate`)) AS `rainRate__merged_matches_neither`
  , SUM(o.`windSpeed` IS NOT NULL) AS `windSpeed__old_nonnull`
  , SUM(w.`windSpeed` IS NOT NULL) AS `windSpeed__wh_nonnull`
  , SUM((o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`=w.`windSpeed`)) AS `windSpeed__source_equal`
  , SUM((o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`<>w.`windSpeed`)) AS `windSpeed__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windSpeed` IS NOT NULL)) AS `windSpeed__merged_nonnull`
  , SUM((m.`windSpeed` IS NOT NULL AND o.`windSpeed` IS NOT NULL AND m.`windSpeed`=o.`windSpeed`)) AS `windSpeed__merged_matches_old`
  , SUM((m.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND m.`windSpeed`=w.`windSpeed`)) AS `windSpeed__merged_matches_wh`
  , SUM((m.`windSpeed` IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND m.`windSpeed`<>o.`windSpeed` AND m.`windSpeed`<>w.`windSpeed`)) AS `windSpeed__merged_matches_neither`
  , SUM(o.`windGust` IS NOT NULL) AS `windGust__old_nonnull`
  , SUM(w.`windGust` IS NOT NULL) AS `windGust__wh_nonnull`
  , SUM((o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`=w.`windGust`)) AS `windGust__source_equal`
  , SUM((o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`<>w.`windGust`)) AS `windGust__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windGust` IS NOT NULL)) AS `windGust__merged_nonnull`
  , SUM((m.`windGust` IS NOT NULL AND o.`windGust` IS NOT NULL AND m.`windGust`=o.`windGust`)) AS `windGust__merged_matches_old`
  , SUM((m.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND m.`windGust`=w.`windGust`)) AS `windGust__merged_matches_wh`
  , SUM((m.`windGust` IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND m.`windGust`<>o.`windGust` AND m.`windGust`<>w.`windGust`)) AS `windGust__merged_matches_neither`
  , SUM(o.`windDir` IS NOT NULL) AS `windDir__old_nonnull`
  , SUM(w.`windDir` IS NOT NULL) AS `windDir__wh_nonnull`
  , SUM((o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`=w.`windDir`)) AS `windDir__source_equal`
  , SUM((o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`<>w.`windDir`)) AS `windDir__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windDir` IS NOT NULL)) AS `windDir__merged_nonnull`
  , SUM((m.`windDir` IS NOT NULL AND o.`windDir` IS NOT NULL AND m.`windDir`=o.`windDir`)) AS `windDir__merged_matches_old`
  , SUM((m.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND m.`windDir`=w.`windDir`)) AS `windDir__merged_matches_wh`
  , SUM((m.`windDir` IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND m.`windDir`<>o.`windDir` AND m.`windDir`<>w.`windDir`)) AS `windDir__merged_matches_neither`
  , SUM(o.`barometer` IS NOT NULL) AS `barometer__old_nonnull`
  , SUM(w.`barometer` IS NOT NULL) AS `barometer__wh_nonnull`
  , SUM((o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`=w.`barometer`)) AS `barometer__source_equal`
  , SUM((o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`<>w.`barometer`)) AS `barometer__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`barometer` IS NOT NULL)) AS `barometer__merged_nonnull`
  , SUM((m.`barometer` IS NOT NULL AND o.`barometer` IS NOT NULL AND m.`barometer`=o.`barometer`)) AS `barometer__merged_matches_old`
  , SUM((m.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND m.`barometer`=w.`barometer`)) AS `barometer__merged_matches_wh`
  , SUM((m.`barometer` IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND m.`barometer`<>o.`barometer` AND m.`barometer`<>w.`barometer`)) AS `barometer__merged_matches_neither`
  , SUM(o.`pressure` IS NOT NULL) AS `pressure__old_nonnull`
  , SUM(w.`pressure` IS NOT NULL) AS `pressure__wh_nonnull`
  , SUM((o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`=w.`pressure`)) AS `pressure__source_equal`
  , SUM((o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`<>w.`pressure`)) AS `pressure__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`pressure` IS NOT NULL)) AS `pressure__merged_nonnull`
  , SUM((m.`pressure` IS NOT NULL AND o.`pressure` IS NOT NULL AND m.`pressure`=o.`pressure`)) AS `pressure__merged_matches_old`
  , SUM((m.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND m.`pressure`=w.`pressure`)) AS `pressure__merged_matches_wh`
  , SUM((m.`pressure` IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND m.`pressure`<>o.`pressure` AND m.`pressure`<>w.`pressure`)) AS `pressure__merged_matches_neither`
  , SUM(o.`altimeter` IS NOT NULL) AS `altimeter__old_nonnull`
  , SUM(w.`altimeter` IS NOT NULL) AS `altimeter__wh_nonnull`
  , SUM((o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`=w.`altimeter`)) AS `altimeter__source_equal`
  , SUM((o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`<>w.`altimeter`)) AS `altimeter__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`altimeter` IS NOT NULL)) AS `altimeter__merged_nonnull`
  , SUM((m.`altimeter` IS NOT NULL AND o.`altimeter` IS NOT NULL AND m.`altimeter`=o.`altimeter`)) AS `altimeter__merged_matches_old`
  , SUM((m.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND m.`altimeter`=w.`altimeter`)) AS `altimeter__merged_matches_wh`
  , SUM((m.`altimeter` IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND m.`altimeter`<>o.`altimeter` AND m.`altimeter`<>w.`altimeter`)) AS `altimeter__merged_matches_neither`
FROM `old_weewx`.`archive` o JOIN `weewx_WH1080`.`archive` w ON w.dateTime=o.dateTime LEFT JOIN `pocasi-loucka.eu_old`.`archive` m ON m.dateTime=o.dateTime WHERE o.dateTime>=1293840000 AND o.dateTime<1325376000;