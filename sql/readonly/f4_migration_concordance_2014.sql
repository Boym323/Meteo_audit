-- READ-ONLY field-level migration concordance for one bounded UTC year.
-- The source schemas are joined by exact dateTime; merged output is a left join.
-- This detects equality/difference only; it does not authorize transformations.
-- 2021 is outside scope; Q1 2018 is not queried.
SELECT 2014 AS utc_year, COUNT(*) AS source_timestamp_pairs
  , SUM(o.`ET` IS NOT NULL) AS `ET__old_nonnull`
  , SUM(w.`ET` IS NOT NULL) AS `ET__wh_nonnull`
  , SUM((o.`ET` IS NOT NULL AND w.`ET` IS NOT NULL)) AS `ET__both_nonnull`
  , SUM((o.`ET` IS NOT NULL AND w.`ET` IS NOT NULL AND o.`ET`=w.`ET`)) AS `ET__source_equal`
  , SUM((o.`ET` IS NOT NULL AND w.`ET` IS NOT NULL AND o.`ET`<>w.`ET`)) AS `ET__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`ET` IS NOT NULL)) AS `ET__merged_nonnull`
  , SUM((m.`ET` IS NOT NULL AND o.`ET` IS NOT NULL AND m.`ET`=o.`ET`)) AS `ET__merged_matches_old`
  , SUM((m.`ET` IS NOT NULL AND w.`ET` IS NOT NULL AND m.`ET`=w.`ET`)) AS `ET__merged_matches_wh`
  , SUM((m.`ET` IS NOT NULL AND o.`ET` IS NOT NULL AND w.`ET` IS NOT NULL AND m.`ET`<>o.`ET` AND m.`ET`<>w.`ET`)) AS `ET__merged_matches_neither`
  , SUM(o.`UV` IS NOT NULL) AS `UV__old_nonnull`
  , SUM(w.`UV` IS NOT NULL) AS `UV__wh_nonnull`
  , SUM((o.`UV` IS NOT NULL AND w.`UV` IS NOT NULL)) AS `UV__both_nonnull`
  , SUM((o.`UV` IS NOT NULL AND w.`UV` IS NOT NULL AND o.`UV`=w.`UV`)) AS `UV__source_equal`
  , SUM((o.`UV` IS NOT NULL AND w.`UV` IS NOT NULL AND o.`UV`<>w.`UV`)) AS `UV__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`UV` IS NOT NULL)) AS `UV__merged_nonnull`
  , SUM((m.`UV` IS NOT NULL AND o.`UV` IS NOT NULL AND m.`UV`=o.`UV`)) AS `UV__merged_matches_old`
  , SUM((m.`UV` IS NOT NULL AND w.`UV` IS NOT NULL AND m.`UV`=w.`UV`)) AS `UV__merged_matches_wh`
  , SUM((m.`UV` IS NOT NULL AND o.`UV` IS NOT NULL AND w.`UV` IS NOT NULL AND m.`UV`<>o.`UV` AND m.`UV`<>w.`UV`)) AS `UV__merged_matches_neither`
  , SUM(o.`altimeter` IS NOT NULL) AS `altimeter__old_nonnull`
  , SUM(w.`altimeter` IS NOT NULL) AS `altimeter__wh_nonnull`
  , SUM((o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL)) AS `altimeter__both_nonnull`
  , SUM((o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`=w.`altimeter`)) AS `altimeter__source_equal`
  , SUM((o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND o.`altimeter`<>w.`altimeter`)) AS `altimeter__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`altimeter` IS NOT NULL)) AS `altimeter__merged_nonnull`
  , SUM((m.`altimeter` IS NOT NULL AND o.`altimeter` IS NOT NULL AND m.`altimeter`=o.`altimeter`)) AS `altimeter__merged_matches_old`
  , SUM((m.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND m.`altimeter`=w.`altimeter`)) AS `altimeter__merged_matches_wh`
  , SUM((m.`altimeter` IS NOT NULL AND o.`altimeter` IS NOT NULL AND w.`altimeter` IS NOT NULL AND m.`altimeter`<>o.`altimeter` AND m.`altimeter`<>w.`altimeter`)) AS `altimeter__merged_matches_neither`
  , SUM(o.`barometer` IS NOT NULL) AS `barometer__old_nonnull`
  , SUM(w.`barometer` IS NOT NULL) AS `barometer__wh_nonnull`
  , SUM((o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL)) AS `barometer__both_nonnull`
  , SUM((o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`=w.`barometer`)) AS `barometer__source_equal`
  , SUM((o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND o.`barometer`<>w.`barometer`)) AS `barometer__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`barometer` IS NOT NULL)) AS `barometer__merged_nonnull`
  , SUM((m.`barometer` IS NOT NULL AND o.`barometer` IS NOT NULL AND m.`barometer`=o.`barometer`)) AS `barometer__merged_matches_old`
  , SUM((m.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND m.`barometer`=w.`barometer`)) AS `barometer__merged_matches_wh`
  , SUM((m.`barometer` IS NOT NULL AND o.`barometer` IS NOT NULL AND w.`barometer` IS NOT NULL AND m.`barometer`<>o.`barometer` AND m.`barometer`<>w.`barometer`)) AS `barometer__merged_matches_neither`
  , SUM(o.`consBatteryVoltage` IS NOT NULL) AS `consBatteryVoltage__old_nonnull`
  , SUM(w.`consBatteryVoltage` IS NOT NULL) AS `consBatteryVoltage__wh_nonnull`
  , SUM((o.`consBatteryVoltage` IS NOT NULL AND w.`consBatteryVoltage` IS NOT NULL)) AS `consBatteryVoltage__both_nonnull`
  , SUM((o.`consBatteryVoltage` IS NOT NULL AND w.`consBatteryVoltage` IS NOT NULL AND o.`consBatteryVoltage`=w.`consBatteryVoltage`)) AS `consBatteryVoltage__source_equal`
  , SUM((o.`consBatteryVoltage` IS NOT NULL AND w.`consBatteryVoltage` IS NOT NULL AND o.`consBatteryVoltage`<>w.`consBatteryVoltage`)) AS `consBatteryVoltage__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`consBatteryVoltage` IS NOT NULL)) AS `consBatteryVoltage__merged_nonnull`
  , SUM((m.`consBatteryVoltage` IS NOT NULL AND o.`consBatteryVoltage` IS NOT NULL AND m.`consBatteryVoltage`=o.`consBatteryVoltage`)) AS `consBatteryVoltage__merged_matches_old`
  , SUM((m.`consBatteryVoltage` IS NOT NULL AND w.`consBatteryVoltage` IS NOT NULL AND m.`consBatteryVoltage`=w.`consBatteryVoltage`)) AS `consBatteryVoltage__merged_matches_wh`
  , SUM((m.`consBatteryVoltage` IS NOT NULL AND o.`consBatteryVoltage` IS NOT NULL AND w.`consBatteryVoltage` IS NOT NULL AND m.`consBatteryVoltage`<>o.`consBatteryVoltage` AND m.`consBatteryVoltage`<>w.`consBatteryVoltage`)) AS `consBatteryVoltage__merged_matches_neither`
  , SUM(o.`dewpoint` IS NOT NULL) AS `dewpoint__old_nonnull`
  , SUM(w.`dewpoint` IS NOT NULL) AS `dewpoint__wh_nonnull`
  , SUM((o.`dewpoint` IS NOT NULL AND w.`dewpoint` IS NOT NULL)) AS `dewpoint__both_nonnull`
  , SUM((o.`dewpoint` IS NOT NULL AND w.`dewpoint` IS NOT NULL AND o.`dewpoint`=w.`dewpoint`)) AS `dewpoint__source_equal`
  , SUM((o.`dewpoint` IS NOT NULL AND w.`dewpoint` IS NOT NULL AND o.`dewpoint`<>w.`dewpoint`)) AS `dewpoint__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`dewpoint` IS NOT NULL)) AS `dewpoint__merged_nonnull`
  , SUM((m.`dewpoint` IS NOT NULL AND o.`dewpoint` IS NOT NULL AND m.`dewpoint`=o.`dewpoint`)) AS `dewpoint__merged_matches_old`
  , SUM((m.`dewpoint` IS NOT NULL AND w.`dewpoint` IS NOT NULL AND m.`dewpoint`=w.`dewpoint`)) AS `dewpoint__merged_matches_wh`
  , SUM((m.`dewpoint` IS NOT NULL AND o.`dewpoint` IS NOT NULL AND w.`dewpoint` IS NOT NULL AND m.`dewpoint`<>o.`dewpoint` AND m.`dewpoint`<>w.`dewpoint`)) AS `dewpoint__merged_matches_neither`
  , SUM(o.`extraHumid1` IS NOT NULL) AS `extraHumid1__old_nonnull`
  , SUM(w.`extraHumid1` IS NOT NULL) AS `extraHumid1__wh_nonnull`
  , SUM((o.`extraHumid1` IS NOT NULL AND w.`extraHumid1` IS NOT NULL)) AS `extraHumid1__both_nonnull`
  , SUM((o.`extraHumid1` IS NOT NULL AND w.`extraHumid1` IS NOT NULL AND o.`extraHumid1`=w.`extraHumid1`)) AS `extraHumid1__source_equal`
  , SUM((o.`extraHumid1` IS NOT NULL AND w.`extraHumid1` IS NOT NULL AND o.`extraHumid1`<>w.`extraHumid1`)) AS `extraHumid1__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`extraHumid1` IS NOT NULL)) AS `extraHumid1__merged_nonnull`
  , SUM((m.`extraHumid1` IS NOT NULL AND o.`extraHumid1` IS NOT NULL AND m.`extraHumid1`=o.`extraHumid1`)) AS `extraHumid1__merged_matches_old`
  , SUM((m.`extraHumid1` IS NOT NULL AND w.`extraHumid1` IS NOT NULL AND m.`extraHumid1`=w.`extraHumid1`)) AS `extraHumid1__merged_matches_wh`
  , SUM((m.`extraHumid1` IS NOT NULL AND o.`extraHumid1` IS NOT NULL AND w.`extraHumid1` IS NOT NULL AND m.`extraHumid1`<>o.`extraHumid1` AND m.`extraHumid1`<>w.`extraHumid1`)) AS `extraHumid1__merged_matches_neither`
  , SUM(o.`extraHumid2` IS NOT NULL) AS `extraHumid2__old_nonnull`
  , SUM(w.`extraHumid2` IS NOT NULL) AS `extraHumid2__wh_nonnull`
  , SUM((o.`extraHumid2` IS NOT NULL AND w.`extraHumid2` IS NOT NULL)) AS `extraHumid2__both_nonnull`
  , SUM((o.`extraHumid2` IS NOT NULL AND w.`extraHumid2` IS NOT NULL AND o.`extraHumid2`=w.`extraHumid2`)) AS `extraHumid2__source_equal`
  , SUM((o.`extraHumid2` IS NOT NULL AND w.`extraHumid2` IS NOT NULL AND o.`extraHumid2`<>w.`extraHumid2`)) AS `extraHumid2__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`extraHumid2` IS NOT NULL)) AS `extraHumid2__merged_nonnull`
  , SUM((m.`extraHumid2` IS NOT NULL AND o.`extraHumid2` IS NOT NULL AND m.`extraHumid2`=o.`extraHumid2`)) AS `extraHumid2__merged_matches_old`
  , SUM((m.`extraHumid2` IS NOT NULL AND w.`extraHumid2` IS NOT NULL AND m.`extraHumid2`=w.`extraHumid2`)) AS `extraHumid2__merged_matches_wh`
  , SUM((m.`extraHumid2` IS NOT NULL AND o.`extraHumid2` IS NOT NULL AND w.`extraHumid2` IS NOT NULL AND m.`extraHumid2`<>o.`extraHumid2` AND m.`extraHumid2`<>w.`extraHumid2`)) AS `extraHumid2__merged_matches_neither`
  , SUM(o.`extraTemp1` IS NOT NULL) AS `extraTemp1__old_nonnull`
  , SUM(w.`extraTemp1` IS NOT NULL) AS `extraTemp1__wh_nonnull`
  , SUM((o.`extraTemp1` IS NOT NULL AND w.`extraTemp1` IS NOT NULL)) AS `extraTemp1__both_nonnull`
  , SUM((o.`extraTemp1` IS NOT NULL AND w.`extraTemp1` IS NOT NULL AND o.`extraTemp1`=w.`extraTemp1`)) AS `extraTemp1__source_equal`
  , SUM((o.`extraTemp1` IS NOT NULL AND w.`extraTemp1` IS NOT NULL AND o.`extraTemp1`<>w.`extraTemp1`)) AS `extraTemp1__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`extraTemp1` IS NOT NULL)) AS `extraTemp1__merged_nonnull`
  , SUM((m.`extraTemp1` IS NOT NULL AND o.`extraTemp1` IS NOT NULL AND m.`extraTemp1`=o.`extraTemp1`)) AS `extraTemp1__merged_matches_old`
  , SUM((m.`extraTemp1` IS NOT NULL AND w.`extraTemp1` IS NOT NULL AND m.`extraTemp1`=w.`extraTemp1`)) AS `extraTemp1__merged_matches_wh`
  , SUM((m.`extraTemp1` IS NOT NULL AND o.`extraTemp1` IS NOT NULL AND w.`extraTemp1` IS NOT NULL AND m.`extraTemp1`<>o.`extraTemp1` AND m.`extraTemp1`<>w.`extraTemp1`)) AS `extraTemp1__merged_matches_neither`
  , SUM(o.`extraTemp2` IS NOT NULL) AS `extraTemp2__old_nonnull`
  , SUM(w.`extraTemp2` IS NOT NULL) AS `extraTemp2__wh_nonnull`
  , SUM((o.`extraTemp2` IS NOT NULL AND w.`extraTemp2` IS NOT NULL)) AS `extraTemp2__both_nonnull`
  , SUM((o.`extraTemp2` IS NOT NULL AND w.`extraTemp2` IS NOT NULL AND o.`extraTemp2`=w.`extraTemp2`)) AS `extraTemp2__source_equal`
  , SUM((o.`extraTemp2` IS NOT NULL AND w.`extraTemp2` IS NOT NULL AND o.`extraTemp2`<>w.`extraTemp2`)) AS `extraTemp2__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`extraTemp2` IS NOT NULL)) AS `extraTemp2__merged_nonnull`
  , SUM((m.`extraTemp2` IS NOT NULL AND o.`extraTemp2` IS NOT NULL AND m.`extraTemp2`=o.`extraTemp2`)) AS `extraTemp2__merged_matches_old`
  , SUM((m.`extraTemp2` IS NOT NULL AND w.`extraTemp2` IS NOT NULL AND m.`extraTemp2`=w.`extraTemp2`)) AS `extraTemp2__merged_matches_wh`
  , SUM((m.`extraTemp2` IS NOT NULL AND o.`extraTemp2` IS NOT NULL AND w.`extraTemp2` IS NOT NULL AND m.`extraTemp2`<>o.`extraTemp2` AND m.`extraTemp2`<>w.`extraTemp2`)) AS `extraTemp2__merged_matches_neither`
  , SUM(o.`extraTemp3` IS NOT NULL) AS `extraTemp3__old_nonnull`
  , SUM(w.`extraTemp3` IS NOT NULL) AS `extraTemp3__wh_nonnull`
  , SUM((o.`extraTemp3` IS NOT NULL AND w.`extraTemp3` IS NOT NULL)) AS `extraTemp3__both_nonnull`
  , SUM((o.`extraTemp3` IS NOT NULL AND w.`extraTemp3` IS NOT NULL AND o.`extraTemp3`=w.`extraTemp3`)) AS `extraTemp3__source_equal`
  , SUM((o.`extraTemp3` IS NOT NULL AND w.`extraTemp3` IS NOT NULL AND o.`extraTemp3`<>w.`extraTemp3`)) AS `extraTemp3__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`extraTemp3` IS NOT NULL)) AS `extraTemp3__merged_nonnull`
  , SUM((m.`extraTemp3` IS NOT NULL AND o.`extraTemp3` IS NOT NULL AND m.`extraTemp3`=o.`extraTemp3`)) AS `extraTemp3__merged_matches_old`
  , SUM((m.`extraTemp3` IS NOT NULL AND w.`extraTemp3` IS NOT NULL AND m.`extraTemp3`=w.`extraTemp3`)) AS `extraTemp3__merged_matches_wh`
  , SUM((m.`extraTemp3` IS NOT NULL AND o.`extraTemp3` IS NOT NULL AND w.`extraTemp3` IS NOT NULL AND m.`extraTemp3`<>o.`extraTemp3` AND m.`extraTemp3`<>w.`extraTemp3`)) AS `extraTemp3__merged_matches_neither`
  , SUM(o.`extraTemp4` IS NOT NULL) AS `extraTemp4__old_nonnull`
  , SUM(w.`extraTemp4` IS NOT NULL) AS `extraTemp4__wh_nonnull`
  , SUM((o.`extraTemp4` IS NOT NULL AND w.`extraTemp4` IS NOT NULL)) AS `extraTemp4__both_nonnull`
  , SUM((o.`extraTemp4` IS NOT NULL AND w.`extraTemp4` IS NOT NULL AND o.`extraTemp4`=w.`extraTemp4`)) AS `extraTemp4__source_equal`
  , SUM((o.`extraTemp4` IS NOT NULL AND w.`extraTemp4` IS NOT NULL AND o.`extraTemp4`<>w.`extraTemp4`)) AS `extraTemp4__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`extraTemp4` IS NOT NULL)) AS `extraTemp4__merged_nonnull`
  , SUM((m.`extraTemp4` IS NOT NULL AND o.`extraTemp4` IS NOT NULL AND m.`extraTemp4`=o.`extraTemp4`)) AS `extraTemp4__merged_matches_old`
  , SUM((m.`extraTemp4` IS NOT NULL AND w.`extraTemp4` IS NOT NULL AND m.`extraTemp4`=w.`extraTemp4`)) AS `extraTemp4__merged_matches_wh`
  , SUM((m.`extraTemp4` IS NOT NULL AND o.`extraTemp4` IS NOT NULL AND w.`extraTemp4` IS NOT NULL AND m.`extraTemp4`<>o.`extraTemp4` AND m.`extraTemp4`<>w.`extraTemp4`)) AS `extraTemp4__merged_matches_neither`
  , SUM(o.`hail` IS NOT NULL) AS `hail__old_nonnull`
  , SUM(w.`hail` IS NOT NULL) AS `hail__wh_nonnull`
  , SUM((o.`hail` IS NOT NULL AND w.`hail` IS NOT NULL)) AS `hail__both_nonnull`
  , SUM((o.`hail` IS NOT NULL AND w.`hail` IS NOT NULL AND o.`hail`=w.`hail`)) AS `hail__source_equal`
  , SUM((o.`hail` IS NOT NULL AND w.`hail` IS NOT NULL AND o.`hail`<>w.`hail`)) AS `hail__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`hail` IS NOT NULL)) AS `hail__merged_nonnull`
  , SUM((m.`hail` IS NOT NULL AND o.`hail` IS NOT NULL AND m.`hail`=o.`hail`)) AS `hail__merged_matches_old`
  , SUM((m.`hail` IS NOT NULL AND w.`hail` IS NOT NULL AND m.`hail`=w.`hail`)) AS `hail__merged_matches_wh`
  , SUM((m.`hail` IS NOT NULL AND o.`hail` IS NOT NULL AND w.`hail` IS NOT NULL AND m.`hail`<>o.`hail` AND m.`hail`<>w.`hail`)) AS `hail__merged_matches_neither`
  , SUM(o.`hailRate` IS NOT NULL) AS `hailRate__old_nonnull`
  , SUM(w.`hailRate` IS NOT NULL) AS `hailRate__wh_nonnull`
  , SUM((o.`hailRate` IS NOT NULL AND w.`hailRate` IS NOT NULL)) AS `hailRate__both_nonnull`
  , SUM((o.`hailRate` IS NOT NULL AND w.`hailRate` IS NOT NULL AND o.`hailRate`=w.`hailRate`)) AS `hailRate__source_equal`
  , SUM((o.`hailRate` IS NOT NULL AND w.`hailRate` IS NOT NULL AND o.`hailRate`<>w.`hailRate`)) AS `hailRate__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`hailRate` IS NOT NULL)) AS `hailRate__merged_nonnull`
  , SUM((m.`hailRate` IS NOT NULL AND o.`hailRate` IS NOT NULL AND m.`hailRate`=o.`hailRate`)) AS `hailRate__merged_matches_old`
  , SUM((m.`hailRate` IS NOT NULL AND w.`hailRate` IS NOT NULL AND m.`hailRate`=w.`hailRate`)) AS `hailRate__merged_matches_wh`
  , SUM((m.`hailRate` IS NOT NULL AND o.`hailRate` IS NOT NULL AND w.`hailRate` IS NOT NULL AND m.`hailRate`<>o.`hailRate` AND m.`hailRate`<>w.`hailRate`)) AS `hailRate__merged_matches_neither`
  , SUM(o.`heatindex` IS NOT NULL) AS `heatindex__old_nonnull`
  , SUM(w.`heatindex` IS NOT NULL) AS `heatindex__wh_nonnull`
  , SUM((o.`heatindex` IS NOT NULL AND w.`heatindex` IS NOT NULL)) AS `heatindex__both_nonnull`
  , SUM((o.`heatindex` IS NOT NULL AND w.`heatindex` IS NOT NULL AND o.`heatindex`=w.`heatindex`)) AS `heatindex__source_equal`
  , SUM((o.`heatindex` IS NOT NULL AND w.`heatindex` IS NOT NULL AND o.`heatindex`<>w.`heatindex`)) AS `heatindex__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`heatindex` IS NOT NULL)) AS `heatindex__merged_nonnull`
  , SUM((m.`heatindex` IS NOT NULL AND o.`heatindex` IS NOT NULL AND m.`heatindex`=o.`heatindex`)) AS `heatindex__merged_matches_old`
  , SUM((m.`heatindex` IS NOT NULL AND w.`heatindex` IS NOT NULL AND m.`heatindex`=w.`heatindex`)) AS `heatindex__merged_matches_wh`
  , SUM((m.`heatindex` IS NOT NULL AND o.`heatindex` IS NOT NULL AND w.`heatindex` IS NOT NULL AND m.`heatindex`<>o.`heatindex` AND m.`heatindex`<>w.`heatindex`)) AS `heatindex__merged_matches_neither`
  , SUM(o.`heatingTemp` IS NOT NULL) AS `heatingTemp__old_nonnull`
  , SUM(w.`heatingTemp` IS NOT NULL) AS `heatingTemp__wh_nonnull`
  , SUM((o.`heatingTemp` IS NOT NULL AND w.`heatingTemp` IS NOT NULL)) AS `heatingTemp__both_nonnull`
  , SUM((o.`heatingTemp` IS NOT NULL AND w.`heatingTemp` IS NOT NULL AND o.`heatingTemp`=w.`heatingTemp`)) AS `heatingTemp__source_equal`
  , SUM((o.`heatingTemp` IS NOT NULL AND w.`heatingTemp` IS NOT NULL AND o.`heatingTemp`<>w.`heatingTemp`)) AS `heatingTemp__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`heatingTemp` IS NOT NULL)) AS `heatingTemp__merged_nonnull`
  , SUM((m.`heatingTemp` IS NOT NULL AND o.`heatingTemp` IS NOT NULL AND m.`heatingTemp`=o.`heatingTemp`)) AS `heatingTemp__merged_matches_old`
  , SUM((m.`heatingTemp` IS NOT NULL AND w.`heatingTemp` IS NOT NULL AND m.`heatingTemp`=w.`heatingTemp`)) AS `heatingTemp__merged_matches_wh`
  , SUM((m.`heatingTemp` IS NOT NULL AND o.`heatingTemp` IS NOT NULL AND w.`heatingTemp` IS NOT NULL AND m.`heatingTemp`<>o.`heatingTemp` AND m.`heatingTemp`<>w.`heatingTemp`)) AS `heatingTemp__merged_matches_neither`
  , SUM(o.`heatingVoltage` IS NOT NULL) AS `heatingVoltage__old_nonnull`
  , SUM(w.`heatingVoltage` IS NOT NULL) AS `heatingVoltage__wh_nonnull`
  , SUM((o.`heatingVoltage` IS NOT NULL AND w.`heatingVoltage` IS NOT NULL)) AS `heatingVoltage__both_nonnull`
  , SUM((o.`heatingVoltage` IS NOT NULL AND w.`heatingVoltage` IS NOT NULL AND o.`heatingVoltage`=w.`heatingVoltage`)) AS `heatingVoltage__source_equal`
  , SUM((o.`heatingVoltage` IS NOT NULL AND w.`heatingVoltage` IS NOT NULL AND o.`heatingVoltage`<>w.`heatingVoltage`)) AS `heatingVoltage__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`heatingVoltage` IS NOT NULL)) AS `heatingVoltage__merged_nonnull`
  , SUM((m.`heatingVoltage` IS NOT NULL AND o.`heatingVoltage` IS NOT NULL AND m.`heatingVoltage`=o.`heatingVoltage`)) AS `heatingVoltage__merged_matches_old`
  , SUM((m.`heatingVoltage` IS NOT NULL AND w.`heatingVoltage` IS NOT NULL AND m.`heatingVoltage`=w.`heatingVoltage`)) AS `heatingVoltage__merged_matches_wh`
  , SUM((m.`heatingVoltage` IS NOT NULL AND o.`heatingVoltage` IS NOT NULL AND w.`heatingVoltage` IS NOT NULL AND m.`heatingVoltage`<>o.`heatingVoltage` AND m.`heatingVoltage`<>w.`heatingVoltage`)) AS `heatingVoltage__merged_matches_neither`
  , SUM(o.`inHumidity` IS NOT NULL) AS `inHumidity__old_nonnull`
  , SUM(w.`inHumidity` IS NOT NULL) AS `inHumidity__wh_nonnull`
  , SUM((o.`inHumidity` IS NOT NULL AND w.`inHumidity` IS NOT NULL)) AS `inHumidity__both_nonnull`
  , SUM((o.`inHumidity` IS NOT NULL AND w.`inHumidity` IS NOT NULL AND o.`inHumidity`=w.`inHumidity`)) AS `inHumidity__source_equal`
  , SUM((o.`inHumidity` IS NOT NULL AND w.`inHumidity` IS NOT NULL AND o.`inHumidity`<>w.`inHumidity`)) AS `inHumidity__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`inHumidity` IS NOT NULL)) AS `inHumidity__merged_nonnull`
  , SUM((m.`inHumidity` IS NOT NULL AND o.`inHumidity` IS NOT NULL AND m.`inHumidity`=o.`inHumidity`)) AS `inHumidity__merged_matches_old`
  , SUM((m.`inHumidity` IS NOT NULL AND w.`inHumidity` IS NOT NULL AND m.`inHumidity`=w.`inHumidity`)) AS `inHumidity__merged_matches_wh`
  , SUM((m.`inHumidity` IS NOT NULL AND o.`inHumidity` IS NOT NULL AND w.`inHumidity` IS NOT NULL AND m.`inHumidity`<>o.`inHumidity` AND m.`inHumidity`<>w.`inHumidity`)) AS `inHumidity__merged_matches_neither`
  , SUM(o.`inTemp` IS NOT NULL) AS `inTemp__old_nonnull`
  , SUM(w.`inTemp` IS NOT NULL) AS `inTemp__wh_nonnull`
  , SUM((o.`inTemp` IS NOT NULL AND w.`inTemp` IS NOT NULL)) AS `inTemp__both_nonnull`
  , SUM((o.`inTemp` IS NOT NULL AND w.`inTemp` IS NOT NULL AND o.`inTemp`=w.`inTemp`)) AS `inTemp__source_equal`
  , SUM((o.`inTemp` IS NOT NULL AND w.`inTemp` IS NOT NULL AND o.`inTemp`<>w.`inTemp`)) AS `inTemp__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`inTemp` IS NOT NULL)) AS `inTemp__merged_nonnull`
  , SUM((m.`inTemp` IS NOT NULL AND o.`inTemp` IS NOT NULL AND m.`inTemp`=o.`inTemp`)) AS `inTemp__merged_matches_old`
  , SUM((m.`inTemp` IS NOT NULL AND w.`inTemp` IS NOT NULL AND m.`inTemp`=w.`inTemp`)) AS `inTemp__merged_matches_wh`
  , SUM((m.`inTemp` IS NOT NULL AND o.`inTemp` IS NOT NULL AND w.`inTemp` IS NOT NULL AND m.`inTemp`<>o.`inTemp` AND m.`inTemp`<>w.`inTemp`)) AS `inTemp__merged_matches_neither`
  , SUM(o.`inTempBatteryStatus` IS NOT NULL) AS `inTempBatteryStatus__old_nonnull`
  , SUM(w.`inTempBatteryStatus` IS NOT NULL) AS `inTempBatteryStatus__wh_nonnull`
  , SUM((o.`inTempBatteryStatus` IS NOT NULL AND w.`inTempBatteryStatus` IS NOT NULL)) AS `inTempBatteryStatus__both_nonnull`
  , SUM((o.`inTempBatteryStatus` IS NOT NULL AND w.`inTempBatteryStatus` IS NOT NULL AND o.`inTempBatteryStatus`=w.`inTempBatteryStatus`)) AS `inTempBatteryStatus__source_equal`
  , SUM((o.`inTempBatteryStatus` IS NOT NULL AND w.`inTempBatteryStatus` IS NOT NULL AND o.`inTempBatteryStatus`<>w.`inTempBatteryStatus`)) AS `inTempBatteryStatus__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`inTempBatteryStatus` IS NOT NULL)) AS `inTempBatteryStatus__merged_nonnull`
  , SUM((m.`inTempBatteryStatus` IS NOT NULL AND o.`inTempBatteryStatus` IS NOT NULL AND m.`inTempBatteryStatus`=o.`inTempBatteryStatus`)) AS `inTempBatteryStatus__merged_matches_old`
  , SUM((m.`inTempBatteryStatus` IS NOT NULL AND w.`inTempBatteryStatus` IS NOT NULL AND m.`inTempBatteryStatus`=w.`inTempBatteryStatus`)) AS `inTempBatteryStatus__merged_matches_wh`
  , SUM((m.`inTempBatteryStatus` IS NOT NULL AND o.`inTempBatteryStatus` IS NOT NULL AND w.`inTempBatteryStatus` IS NOT NULL AND m.`inTempBatteryStatus`<>o.`inTempBatteryStatus` AND m.`inTempBatteryStatus`<>w.`inTempBatteryStatus`)) AS `inTempBatteryStatus__merged_matches_neither`
  , SUM(o.`leafTemp1` IS NOT NULL) AS `leafTemp1__old_nonnull`
  , SUM(w.`leafTemp1` IS NOT NULL) AS `leafTemp1__wh_nonnull`
  , SUM((o.`leafTemp1` IS NOT NULL AND w.`leafTemp1` IS NOT NULL)) AS `leafTemp1__both_nonnull`
  , SUM((o.`leafTemp1` IS NOT NULL AND w.`leafTemp1` IS NOT NULL AND o.`leafTemp1`=w.`leafTemp1`)) AS `leafTemp1__source_equal`
  , SUM((o.`leafTemp1` IS NOT NULL AND w.`leafTemp1` IS NOT NULL AND o.`leafTemp1`<>w.`leafTemp1`)) AS `leafTemp1__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`leafTemp1` IS NOT NULL)) AS `leafTemp1__merged_nonnull`
  , SUM((m.`leafTemp1` IS NOT NULL AND o.`leafTemp1` IS NOT NULL AND m.`leafTemp1`=o.`leafTemp1`)) AS `leafTemp1__merged_matches_old`
  , SUM((m.`leafTemp1` IS NOT NULL AND w.`leafTemp1` IS NOT NULL AND m.`leafTemp1`=w.`leafTemp1`)) AS `leafTemp1__merged_matches_wh`
  , SUM((m.`leafTemp1` IS NOT NULL AND o.`leafTemp1` IS NOT NULL AND w.`leafTemp1` IS NOT NULL AND m.`leafTemp1`<>o.`leafTemp1` AND m.`leafTemp1`<>w.`leafTemp1`)) AS `leafTemp1__merged_matches_neither`
  , SUM(o.`leafTemp2` IS NOT NULL) AS `leafTemp2__old_nonnull`
  , SUM(w.`leafTemp2` IS NOT NULL) AS `leafTemp2__wh_nonnull`
  , SUM((o.`leafTemp2` IS NOT NULL AND w.`leafTemp2` IS NOT NULL)) AS `leafTemp2__both_nonnull`
  , SUM((o.`leafTemp2` IS NOT NULL AND w.`leafTemp2` IS NOT NULL AND o.`leafTemp2`=w.`leafTemp2`)) AS `leafTemp2__source_equal`
  , SUM((o.`leafTemp2` IS NOT NULL AND w.`leafTemp2` IS NOT NULL AND o.`leafTemp2`<>w.`leafTemp2`)) AS `leafTemp2__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`leafTemp2` IS NOT NULL)) AS `leafTemp2__merged_nonnull`
  , SUM((m.`leafTemp2` IS NOT NULL AND o.`leafTemp2` IS NOT NULL AND m.`leafTemp2`=o.`leafTemp2`)) AS `leafTemp2__merged_matches_old`
  , SUM((m.`leafTemp2` IS NOT NULL AND w.`leafTemp2` IS NOT NULL AND m.`leafTemp2`=w.`leafTemp2`)) AS `leafTemp2__merged_matches_wh`
  , SUM((m.`leafTemp2` IS NOT NULL AND o.`leafTemp2` IS NOT NULL AND w.`leafTemp2` IS NOT NULL AND m.`leafTemp2`<>o.`leafTemp2` AND m.`leafTemp2`<>w.`leafTemp2`)) AS `leafTemp2__merged_matches_neither`
  , SUM(o.`leafWet1` IS NOT NULL) AS `leafWet1__old_nonnull`
  , SUM(w.`leafWet1` IS NOT NULL) AS `leafWet1__wh_nonnull`
  , SUM((o.`leafWet1` IS NOT NULL AND w.`leafWet1` IS NOT NULL)) AS `leafWet1__both_nonnull`
  , SUM((o.`leafWet1` IS NOT NULL AND w.`leafWet1` IS NOT NULL AND o.`leafWet1`=w.`leafWet1`)) AS `leafWet1__source_equal`
  , SUM((o.`leafWet1` IS NOT NULL AND w.`leafWet1` IS NOT NULL AND o.`leafWet1`<>w.`leafWet1`)) AS `leafWet1__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`leafWet1` IS NOT NULL)) AS `leafWet1__merged_nonnull`
  , SUM((m.`leafWet1` IS NOT NULL AND o.`leafWet1` IS NOT NULL AND m.`leafWet1`=o.`leafWet1`)) AS `leafWet1__merged_matches_old`
  , SUM((m.`leafWet1` IS NOT NULL AND w.`leafWet1` IS NOT NULL AND m.`leafWet1`=w.`leafWet1`)) AS `leafWet1__merged_matches_wh`
  , SUM((m.`leafWet1` IS NOT NULL AND o.`leafWet1` IS NOT NULL AND w.`leafWet1` IS NOT NULL AND m.`leafWet1`<>o.`leafWet1` AND m.`leafWet1`<>w.`leafWet1`)) AS `leafWet1__merged_matches_neither`
  , SUM(o.`leafWet2` IS NOT NULL) AS `leafWet2__old_nonnull`
  , SUM(w.`leafWet2` IS NOT NULL) AS `leafWet2__wh_nonnull`
  , SUM((o.`leafWet2` IS NOT NULL AND w.`leafWet2` IS NOT NULL)) AS `leafWet2__both_nonnull`
  , SUM((o.`leafWet2` IS NOT NULL AND w.`leafWet2` IS NOT NULL AND o.`leafWet2`=w.`leafWet2`)) AS `leafWet2__source_equal`
  , SUM((o.`leafWet2` IS NOT NULL AND w.`leafWet2` IS NOT NULL AND o.`leafWet2`<>w.`leafWet2`)) AS `leafWet2__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`leafWet2` IS NOT NULL)) AS `leafWet2__merged_nonnull`
  , SUM((m.`leafWet2` IS NOT NULL AND o.`leafWet2` IS NOT NULL AND m.`leafWet2`=o.`leafWet2`)) AS `leafWet2__merged_matches_old`
  , SUM((m.`leafWet2` IS NOT NULL AND w.`leafWet2` IS NOT NULL AND m.`leafWet2`=w.`leafWet2`)) AS `leafWet2__merged_matches_wh`
  , SUM((m.`leafWet2` IS NOT NULL AND o.`leafWet2` IS NOT NULL AND w.`leafWet2` IS NOT NULL AND m.`leafWet2`<>o.`leafWet2` AND m.`leafWet2`<>w.`leafWet2`)) AS `leafWet2__merged_matches_neither`
  , SUM(o.`outHumidity` IS NOT NULL) AS `outHumidity__old_nonnull`
  , SUM(w.`outHumidity` IS NOT NULL) AS `outHumidity__wh_nonnull`
  , SUM((o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL)) AS `outHumidity__both_nonnull`
  , SUM((o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`=w.`outHumidity`)) AS `outHumidity__source_equal`
  , SUM((o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND o.`outHumidity`<>w.`outHumidity`)) AS `outHumidity__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`outHumidity` IS NOT NULL)) AS `outHumidity__merged_nonnull`
  , SUM((m.`outHumidity` IS NOT NULL AND o.`outHumidity` IS NOT NULL AND m.`outHumidity`=o.`outHumidity`)) AS `outHumidity__merged_matches_old`
  , SUM((m.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND m.`outHumidity`=w.`outHumidity`)) AS `outHumidity__merged_matches_wh`
  , SUM((m.`outHumidity` IS NOT NULL AND o.`outHumidity` IS NOT NULL AND w.`outHumidity` IS NOT NULL AND m.`outHumidity`<>o.`outHumidity` AND m.`outHumidity`<>w.`outHumidity`)) AS `outHumidity__merged_matches_neither`
  , SUM(o.`outTemp` IS NOT NULL) AS `outTemp__old_nonnull`
  , SUM(w.`outTemp` IS NOT NULL) AS `outTemp__wh_nonnull`
  , SUM((o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL)) AS `outTemp__both_nonnull`
  , SUM((o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`=w.`outTemp`)) AS `outTemp__source_equal`
  , SUM((o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND o.`outTemp`<>w.`outTemp`)) AS `outTemp__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`outTemp` IS NOT NULL)) AS `outTemp__merged_nonnull`
  , SUM((m.`outTemp` IS NOT NULL AND o.`outTemp` IS NOT NULL AND m.`outTemp`=o.`outTemp`)) AS `outTemp__merged_matches_old`
  , SUM((m.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND m.`outTemp`=w.`outTemp`)) AS `outTemp__merged_matches_wh`
  , SUM((m.`outTemp` IS NOT NULL AND o.`outTemp` IS NOT NULL AND w.`outTemp` IS NOT NULL AND m.`outTemp`<>o.`outTemp` AND m.`outTemp`<>w.`outTemp`)) AS `outTemp__merged_matches_neither`
  , SUM(o.`outTempBatteryStatus` IS NOT NULL) AS `outTempBatteryStatus__old_nonnull`
  , SUM(w.`outTempBatteryStatus` IS NOT NULL) AS `outTempBatteryStatus__wh_nonnull`
  , SUM((o.`outTempBatteryStatus` IS NOT NULL AND w.`outTempBatteryStatus` IS NOT NULL)) AS `outTempBatteryStatus__both_nonnull`
  , SUM((o.`outTempBatteryStatus` IS NOT NULL AND w.`outTempBatteryStatus` IS NOT NULL AND o.`outTempBatteryStatus`=w.`outTempBatteryStatus`)) AS `outTempBatteryStatus__source_equal`
  , SUM((o.`outTempBatteryStatus` IS NOT NULL AND w.`outTempBatteryStatus` IS NOT NULL AND o.`outTempBatteryStatus`<>w.`outTempBatteryStatus`)) AS `outTempBatteryStatus__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`outTempBatteryStatus` IS NOT NULL)) AS `outTempBatteryStatus__merged_nonnull`
  , SUM((m.`outTempBatteryStatus` IS NOT NULL AND o.`outTempBatteryStatus` IS NOT NULL AND m.`outTempBatteryStatus`=o.`outTempBatteryStatus`)) AS `outTempBatteryStatus__merged_matches_old`
  , SUM((m.`outTempBatteryStatus` IS NOT NULL AND w.`outTempBatteryStatus` IS NOT NULL AND m.`outTempBatteryStatus`=w.`outTempBatteryStatus`)) AS `outTempBatteryStatus__merged_matches_wh`
  , SUM((m.`outTempBatteryStatus` IS NOT NULL AND o.`outTempBatteryStatus` IS NOT NULL AND w.`outTempBatteryStatus` IS NOT NULL AND m.`outTempBatteryStatus`<>o.`outTempBatteryStatus` AND m.`outTempBatteryStatus`<>w.`outTempBatteryStatus`)) AS `outTempBatteryStatus__merged_matches_neither`
  , SUM(o.`pressure` IS NOT NULL) AS `pressure__old_nonnull`
  , SUM(w.`pressure` IS NOT NULL) AS `pressure__wh_nonnull`
  , SUM((o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL)) AS `pressure__both_nonnull`
  , SUM((o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`=w.`pressure`)) AS `pressure__source_equal`
  , SUM((o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND o.`pressure`<>w.`pressure`)) AS `pressure__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`pressure` IS NOT NULL)) AS `pressure__merged_nonnull`
  , SUM((m.`pressure` IS NOT NULL AND o.`pressure` IS NOT NULL AND m.`pressure`=o.`pressure`)) AS `pressure__merged_matches_old`
  , SUM((m.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND m.`pressure`=w.`pressure`)) AS `pressure__merged_matches_wh`
  , SUM((m.`pressure` IS NOT NULL AND o.`pressure` IS NOT NULL AND w.`pressure` IS NOT NULL AND m.`pressure`<>o.`pressure` AND m.`pressure`<>w.`pressure`)) AS `pressure__merged_matches_neither`
  , SUM(o.`radiation` IS NOT NULL) AS `radiation__old_nonnull`
  , SUM(w.`radiation` IS NOT NULL) AS `radiation__wh_nonnull`
  , SUM((o.`radiation` IS NOT NULL AND w.`radiation` IS NOT NULL)) AS `radiation__both_nonnull`
  , SUM((o.`radiation` IS NOT NULL AND w.`radiation` IS NOT NULL AND o.`radiation`=w.`radiation`)) AS `radiation__source_equal`
  , SUM((o.`radiation` IS NOT NULL AND w.`radiation` IS NOT NULL AND o.`radiation`<>w.`radiation`)) AS `radiation__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`radiation` IS NOT NULL)) AS `radiation__merged_nonnull`
  , SUM((m.`radiation` IS NOT NULL AND o.`radiation` IS NOT NULL AND m.`radiation`=o.`radiation`)) AS `radiation__merged_matches_old`
  , SUM((m.`radiation` IS NOT NULL AND w.`radiation` IS NOT NULL AND m.`radiation`=w.`radiation`)) AS `radiation__merged_matches_wh`
  , SUM((m.`radiation` IS NOT NULL AND o.`radiation` IS NOT NULL AND w.`radiation` IS NOT NULL AND m.`radiation`<>o.`radiation` AND m.`radiation`<>w.`radiation`)) AS `radiation__merged_matches_neither`
  , SUM(o.`rain` IS NOT NULL) AS `rain__old_nonnull`
  , SUM(w.`rain` IS NOT NULL) AS `rain__wh_nonnull`
  , SUM((o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL)) AS `rain__both_nonnull`
  , SUM((o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`=w.`rain`)) AS `rain__source_equal`
  , SUM((o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND o.`rain`<>w.`rain`)) AS `rain__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`rain` IS NOT NULL)) AS `rain__merged_nonnull`
  , SUM((m.`rain` IS NOT NULL AND o.`rain` IS NOT NULL AND m.`rain`=o.`rain`)) AS `rain__merged_matches_old`
  , SUM((m.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND m.`rain`=w.`rain`)) AS `rain__merged_matches_wh`
  , SUM((m.`rain` IS NOT NULL AND o.`rain` IS NOT NULL AND w.`rain` IS NOT NULL AND m.`rain`<>o.`rain` AND m.`rain`<>w.`rain`)) AS `rain__merged_matches_neither`
  , SUM(o.`rainBatteryStatus` IS NOT NULL) AS `rainBatteryStatus__old_nonnull`
  , SUM(w.`rainBatteryStatus` IS NOT NULL) AS `rainBatteryStatus__wh_nonnull`
  , SUM((o.`rainBatteryStatus` IS NOT NULL AND w.`rainBatteryStatus` IS NOT NULL)) AS `rainBatteryStatus__both_nonnull`
  , SUM((o.`rainBatteryStatus` IS NOT NULL AND w.`rainBatteryStatus` IS NOT NULL AND o.`rainBatteryStatus`=w.`rainBatteryStatus`)) AS `rainBatteryStatus__source_equal`
  , SUM((o.`rainBatteryStatus` IS NOT NULL AND w.`rainBatteryStatus` IS NOT NULL AND o.`rainBatteryStatus`<>w.`rainBatteryStatus`)) AS `rainBatteryStatus__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`rainBatteryStatus` IS NOT NULL)) AS `rainBatteryStatus__merged_nonnull`
  , SUM((m.`rainBatteryStatus` IS NOT NULL AND o.`rainBatteryStatus` IS NOT NULL AND m.`rainBatteryStatus`=o.`rainBatteryStatus`)) AS `rainBatteryStatus__merged_matches_old`
  , SUM((m.`rainBatteryStatus` IS NOT NULL AND w.`rainBatteryStatus` IS NOT NULL AND m.`rainBatteryStatus`=w.`rainBatteryStatus`)) AS `rainBatteryStatus__merged_matches_wh`
  , SUM((m.`rainBatteryStatus` IS NOT NULL AND o.`rainBatteryStatus` IS NOT NULL AND w.`rainBatteryStatus` IS NOT NULL AND m.`rainBatteryStatus`<>o.`rainBatteryStatus` AND m.`rainBatteryStatus`<>w.`rainBatteryStatus`)) AS `rainBatteryStatus__merged_matches_neither`
  , SUM(o.`rainRate` IS NOT NULL) AS `rainRate__old_nonnull`
  , SUM(w.`rainRate` IS NOT NULL) AS `rainRate__wh_nonnull`
  , SUM((o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL)) AS `rainRate__both_nonnull`
  , SUM((o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`=w.`rainRate`)) AS `rainRate__source_equal`
  , SUM((o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND o.`rainRate`<>w.`rainRate`)) AS `rainRate__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`rainRate` IS NOT NULL)) AS `rainRate__merged_nonnull`
  , SUM((m.`rainRate` IS NOT NULL AND o.`rainRate` IS NOT NULL AND m.`rainRate`=o.`rainRate`)) AS `rainRate__merged_matches_old`
  , SUM((m.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND m.`rainRate`=w.`rainRate`)) AS `rainRate__merged_matches_wh`
  , SUM((m.`rainRate` IS NOT NULL AND o.`rainRate` IS NOT NULL AND w.`rainRate` IS NOT NULL AND m.`rainRate`<>o.`rainRate` AND m.`rainRate`<>w.`rainRate`)) AS `rainRate__merged_matches_neither`
  , SUM(o.`referenceVoltage` IS NOT NULL) AS `referenceVoltage__old_nonnull`
  , SUM(w.`referenceVoltage` IS NOT NULL) AS `referenceVoltage__wh_nonnull`
  , SUM((o.`referenceVoltage` IS NOT NULL AND w.`referenceVoltage` IS NOT NULL)) AS `referenceVoltage__both_nonnull`
  , SUM((o.`referenceVoltage` IS NOT NULL AND w.`referenceVoltage` IS NOT NULL AND o.`referenceVoltage`=w.`referenceVoltage`)) AS `referenceVoltage__source_equal`
  , SUM((o.`referenceVoltage` IS NOT NULL AND w.`referenceVoltage` IS NOT NULL AND o.`referenceVoltage`<>w.`referenceVoltage`)) AS `referenceVoltage__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`referenceVoltage` IS NOT NULL)) AS `referenceVoltage__merged_nonnull`
  , SUM((m.`referenceVoltage` IS NOT NULL AND o.`referenceVoltage` IS NOT NULL AND m.`referenceVoltage`=o.`referenceVoltage`)) AS `referenceVoltage__merged_matches_old`
  , SUM((m.`referenceVoltage` IS NOT NULL AND w.`referenceVoltage` IS NOT NULL AND m.`referenceVoltage`=w.`referenceVoltage`)) AS `referenceVoltage__merged_matches_wh`
  , SUM((m.`referenceVoltage` IS NOT NULL AND o.`referenceVoltage` IS NOT NULL AND w.`referenceVoltage` IS NOT NULL AND m.`referenceVoltage`<>o.`referenceVoltage` AND m.`referenceVoltage`<>w.`referenceVoltage`)) AS `referenceVoltage__merged_matches_neither`
  , SUM(o.`rxCheckPercent` IS NOT NULL) AS `rxCheckPercent__old_nonnull`
  , SUM(w.`rxCheckPercent` IS NOT NULL) AS `rxCheckPercent__wh_nonnull`
  , SUM((o.`rxCheckPercent` IS NOT NULL AND w.`rxCheckPercent` IS NOT NULL)) AS `rxCheckPercent__both_nonnull`
  , SUM((o.`rxCheckPercent` IS NOT NULL AND w.`rxCheckPercent` IS NOT NULL AND o.`rxCheckPercent`=w.`rxCheckPercent`)) AS `rxCheckPercent__source_equal`
  , SUM((o.`rxCheckPercent` IS NOT NULL AND w.`rxCheckPercent` IS NOT NULL AND o.`rxCheckPercent`<>w.`rxCheckPercent`)) AS `rxCheckPercent__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`rxCheckPercent` IS NOT NULL)) AS `rxCheckPercent__merged_nonnull`
  , SUM((m.`rxCheckPercent` IS NOT NULL AND o.`rxCheckPercent` IS NOT NULL AND m.`rxCheckPercent`=o.`rxCheckPercent`)) AS `rxCheckPercent__merged_matches_old`
  , SUM((m.`rxCheckPercent` IS NOT NULL AND w.`rxCheckPercent` IS NOT NULL AND m.`rxCheckPercent`=w.`rxCheckPercent`)) AS `rxCheckPercent__merged_matches_wh`
  , SUM((m.`rxCheckPercent` IS NOT NULL AND o.`rxCheckPercent` IS NOT NULL AND w.`rxCheckPercent` IS NOT NULL AND m.`rxCheckPercent`<>o.`rxCheckPercent` AND m.`rxCheckPercent`<>w.`rxCheckPercent`)) AS `rxCheckPercent__merged_matches_neither`
  , SUM(o.`soilMoist1` IS NOT NULL) AS `soilMoist1__old_nonnull`
  , SUM(w.`soilMoist1` IS NOT NULL) AS `soilMoist1__wh_nonnull`
  , SUM((o.`soilMoist1` IS NOT NULL AND w.`soilMoist1` IS NOT NULL)) AS `soilMoist1__both_nonnull`
  , SUM((o.`soilMoist1` IS NOT NULL AND w.`soilMoist1` IS NOT NULL AND o.`soilMoist1`=w.`soilMoist1`)) AS `soilMoist1__source_equal`
  , SUM((o.`soilMoist1` IS NOT NULL AND w.`soilMoist1` IS NOT NULL AND o.`soilMoist1`<>w.`soilMoist1`)) AS `soilMoist1__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilMoist1` IS NOT NULL)) AS `soilMoist1__merged_nonnull`
  , SUM((m.`soilMoist1` IS NOT NULL AND o.`soilMoist1` IS NOT NULL AND m.`soilMoist1`=o.`soilMoist1`)) AS `soilMoist1__merged_matches_old`
  , SUM((m.`soilMoist1` IS NOT NULL AND w.`soilMoist1` IS NOT NULL AND m.`soilMoist1`=w.`soilMoist1`)) AS `soilMoist1__merged_matches_wh`
  , SUM((m.`soilMoist1` IS NOT NULL AND o.`soilMoist1` IS NOT NULL AND w.`soilMoist1` IS NOT NULL AND m.`soilMoist1`<>o.`soilMoist1` AND m.`soilMoist1`<>w.`soilMoist1`)) AS `soilMoist1__merged_matches_neither`
  , SUM(o.`soilMoist2` IS NOT NULL) AS `soilMoist2__old_nonnull`
  , SUM(w.`soilMoist2` IS NOT NULL) AS `soilMoist2__wh_nonnull`
  , SUM((o.`soilMoist2` IS NOT NULL AND w.`soilMoist2` IS NOT NULL)) AS `soilMoist2__both_nonnull`
  , SUM((o.`soilMoist2` IS NOT NULL AND w.`soilMoist2` IS NOT NULL AND o.`soilMoist2`=w.`soilMoist2`)) AS `soilMoist2__source_equal`
  , SUM((o.`soilMoist2` IS NOT NULL AND w.`soilMoist2` IS NOT NULL AND o.`soilMoist2`<>w.`soilMoist2`)) AS `soilMoist2__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilMoist2` IS NOT NULL)) AS `soilMoist2__merged_nonnull`
  , SUM((m.`soilMoist2` IS NOT NULL AND o.`soilMoist2` IS NOT NULL AND m.`soilMoist2`=o.`soilMoist2`)) AS `soilMoist2__merged_matches_old`
  , SUM((m.`soilMoist2` IS NOT NULL AND w.`soilMoist2` IS NOT NULL AND m.`soilMoist2`=w.`soilMoist2`)) AS `soilMoist2__merged_matches_wh`
  , SUM((m.`soilMoist2` IS NOT NULL AND o.`soilMoist2` IS NOT NULL AND w.`soilMoist2` IS NOT NULL AND m.`soilMoist2`<>o.`soilMoist2` AND m.`soilMoist2`<>w.`soilMoist2`)) AS `soilMoist2__merged_matches_neither`
  , SUM(o.`soilMoist3` IS NOT NULL) AS `soilMoist3__old_nonnull`
  , SUM(w.`soilMoist3` IS NOT NULL) AS `soilMoist3__wh_nonnull`
  , SUM((o.`soilMoist3` IS NOT NULL AND w.`soilMoist3` IS NOT NULL)) AS `soilMoist3__both_nonnull`
  , SUM((o.`soilMoist3` IS NOT NULL AND w.`soilMoist3` IS NOT NULL AND o.`soilMoist3`=w.`soilMoist3`)) AS `soilMoist3__source_equal`
  , SUM((o.`soilMoist3` IS NOT NULL AND w.`soilMoist3` IS NOT NULL AND o.`soilMoist3`<>w.`soilMoist3`)) AS `soilMoist3__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilMoist3` IS NOT NULL)) AS `soilMoist3__merged_nonnull`
  , SUM((m.`soilMoist3` IS NOT NULL AND o.`soilMoist3` IS NOT NULL AND m.`soilMoist3`=o.`soilMoist3`)) AS `soilMoist3__merged_matches_old`
  , SUM((m.`soilMoist3` IS NOT NULL AND w.`soilMoist3` IS NOT NULL AND m.`soilMoist3`=w.`soilMoist3`)) AS `soilMoist3__merged_matches_wh`
  , SUM((m.`soilMoist3` IS NOT NULL AND o.`soilMoist3` IS NOT NULL AND w.`soilMoist3` IS NOT NULL AND m.`soilMoist3`<>o.`soilMoist3` AND m.`soilMoist3`<>w.`soilMoist3`)) AS `soilMoist3__merged_matches_neither`
  , SUM(o.`soilMoist4` IS NOT NULL) AS `soilMoist4__old_nonnull`
  , SUM(w.`soilMoist4` IS NOT NULL) AS `soilMoist4__wh_nonnull`
  , SUM((o.`soilMoist4` IS NOT NULL AND w.`soilMoist4` IS NOT NULL)) AS `soilMoist4__both_nonnull`
  , SUM((o.`soilMoist4` IS NOT NULL AND w.`soilMoist4` IS NOT NULL AND o.`soilMoist4`=w.`soilMoist4`)) AS `soilMoist4__source_equal`
  , SUM((o.`soilMoist4` IS NOT NULL AND w.`soilMoist4` IS NOT NULL AND o.`soilMoist4`<>w.`soilMoist4`)) AS `soilMoist4__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilMoist4` IS NOT NULL)) AS `soilMoist4__merged_nonnull`
  , SUM((m.`soilMoist4` IS NOT NULL AND o.`soilMoist4` IS NOT NULL AND m.`soilMoist4`=o.`soilMoist4`)) AS `soilMoist4__merged_matches_old`
  , SUM((m.`soilMoist4` IS NOT NULL AND w.`soilMoist4` IS NOT NULL AND m.`soilMoist4`=w.`soilMoist4`)) AS `soilMoist4__merged_matches_wh`
  , SUM((m.`soilMoist4` IS NOT NULL AND o.`soilMoist4` IS NOT NULL AND w.`soilMoist4` IS NOT NULL AND m.`soilMoist4`<>o.`soilMoist4` AND m.`soilMoist4`<>w.`soilMoist4`)) AS `soilMoist4__merged_matches_neither`
  , SUM(o.`soilTemp1` IS NOT NULL) AS `soilTemp1__old_nonnull`
  , SUM(w.`soilTemp1` IS NOT NULL) AS `soilTemp1__wh_nonnull`
  , SUM((o.`soilTemp1` IS NOT NULL AND w.`soilTemp1` IS NOT NULL)) AS `soilTemp1__both_nonnull`
  , SUM((o.`soilTemp1` IS NOT NULL AND w.`soilTemp1` IS NOT NULL AND o.`soilTemp1`=w.`soilTemp1`)) AS `soilTemp1__source_equal`
  , SUM((o.`soilTemp1` IS NOT NULL AND w.`soilTemp1` IS NOT NULL AND o.`soilTemp1`<>w.`soilTemp1`)) AS `soilTemp1__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilTemp1` IS NOT NULL)) AS `soilTemp1__merged_nonnull`
  , SUM((m.`soilTemp1` IS NOT NULL AND o.`soilTemp1` IS NOT NULL AND m.`soilTemp1`=o.`soilTemp1`)) AS `soilTemp1__merged_matches_old`
  , SUM((m.`soilTemp1` IS NOT NULL AND w.`soilTemp1` IS NOT NULL AND m.`soilTemp1`=w.`soilTemp1`)) AS `soilTemp1__merged_matches_wh`
  , SUM((m.`soilTemp1` IS NOT NULL AND o.`soilTemp1` IS NOT NULL AND w.`soilTemp1` IS NOT NULL AND m.`soilTemp1`<>o.`soilTemp1` AND m.`soilTemp1`<>w.`soilTemp1`)) AS `soilTemp1__merged_matches_neither`
  , SUM(o.`soilTemp2` IS NOT NULL) AS `soilTemp2__old_nonnull`
  , SUM(w.`soilTemp2` IS NOT NULL) AS `soilTemp2__wh_nonnull`
  , SUM((o.`soilTemp2` IS NOT NULL AND w.`soilTemp2` IS NOT NULL)) AS `soilTemp2__both_nonnull`
  , SUM((o.`soilTemp2` IS NOT NULL AND w.`soilTemp2` IS NOT NULL AND o.`soilTemp2`=w.`soilTemp2`)) AS `soilTemp2__source_equal`
  , SUM((o.`soilTemp2` IS NOT NULL AND w.`soilTemp2` IS NOT NULL AND o.`soilTemp2`<>w.`soilTemp2`)) AS `soilTemp2__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilTemp2` IS NOT NULL)) AS `soilTemp2__merged_nonnull`
  , SUM((m.`soilTemp2` IS NOT NULL AND o.`soilTemp2` IS NOT NULL AND m.`soilTemp2`=o.`soilTemp2`)) AS `soilTemp2__merged_matches_old`
  , SUM((m.`soilTemp2` IS NOT NULL AND w.`soilTemp2` IS NOT NULL AND m.`soilTemp2`=w.`soilTemp2`)) AS `soilTemp2__merged_matches_wh`
  , SUM((m.`soilTemp2` IS NOT NULL AND o.`soilTemp2` IS NOT NULL AND w.`soilTemp2` IS NOT NULL AND m.`soilTemp2`<>o.`soilTemp2` AND m.`soilTemp2`<>w.`soilTemp2`)) AS `soilTemp2__merged_matches_neither`
  , SUM(o.`soilTemp3` IS NOT NULL) AS `soilTemp3__old_nonnull`
  , SUM(w.`soilTemp3` IS NOT NULL) AS `soilTemp3__wh_nonnull`
  , SUM((o.`soilTemp3` IS NOT NULL AND w.`soilTemp3` IS NOT NULL)) AS `soilTemp3__both_nonnull`
  , SUM((o.`soilTemp3` IS NOT NULL AND w.`soilTemp3` IS NOT NULL AND o.`soilTemp3`=w.`soilTemp3`)) AS `soilTemp3__source_equal`
  , SUM((o.`soilTemp3` IS NOT NULL AND w.`soilTemp3` IS NOT NULL AND o.`soilTemp3`<>w.`soilTemp3`)) AS `soilTemp3__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilTemp3` IS NOT NULL)) AS `soilTemp3__merged_nonnull`
  , SUM((m.`soilTemp3` IS NOT NULL AND o.`soilTemp3` IS NOT NULL AND m.`soilTemp3`=o.`soilTemp3`)) AS `soilTemp3__merged_matches_old`
  , SUM((m.`soilTemp3` IS NOT NULL AND w.`soilTemp3` IS NOT NULL AND m.`soilTemp3`=w.`soilTemp3`)) AS `soilTemp3__merged_matches_wh`
  , SUM((m.`soilTemp3` IS NOT NULL AND o.`soilTemp3` IS NOT NULL AND w.`soilTemp3` IS NOT NULL AND m.`soilTemp3`<>o.`soilTemp3` AND m.`soilTemp3`<>w.`soilTemp3`)) AS `soilTemp3__merged_matches_neither`
  , SUM(o.`soilTemp4` IS NOT NULL) AS `soilTemp4__old_nonnull`
  , SUM(w.`soilTemp4` IS NOT NULL) AS `soilTemp4__wh_nonnull`
  , SUM((o.`soilTemp4` IS NOT NULL AND w.`soilTemp4` IS NOT NULL)) AS `soilTemp4__both_nonnull`
  , SUM((o.`soilTemp4` IS NOT NULL AND w.`soilTemp4` IS NOT NULL AND o.`soilTemp4`=w.`soilTemp4`)) AS `soilTemp4__source_equal`
  , SUM((o.`soilTemp4` IS NOT NULL AND w.`soilTemp4` IS NOT NULL AND o.`soilTemp4`<>w.`soilTemp4`)) AS `soilTemp4__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`soilTemp4` IS NOT NULL)) AS `soilTemp4__merged_nonnull`
  , SUM((m.`soilTemp4` IS NOT NULL AND o.`soilTemp4` IS NOT NULL AND m.`soilTemp4`=o.`soilTemp4`)) AS `soilTemp4__merged_matches_old`
  , SUM((m.`soilTemp4` IS NOT NULL AND w.`soilTemp4` IS NOT NULL AND m.`soilTemp4`=w.`soilTemp4`)) AS `soilTemp4__merged_matches_wh`
  , SUM((m.`soilTemp4` IS NOT NULL AND o.`soilTemp4` IS NOT NULL AND w.`soilTemp4` IS NOT NULL AND m.`soilTemp4`<>o.`soilTemp4` AND m.`soilTemp4`<>w.`soilTemp4`)) AS `soilTemp4__merged_matches_neither`
  , SUM(o.`supplyVoltage` IS NOT NULL) AS `supplyVoltage__old_nonnull`
  , SUM(w.`supplyVoltage` IS NOT NULL) AS `supplyVoltage__wh_nonnull`
  , SUM((o.`supplyVoltage` IS NOT NULL AND w.`supplyVoltage` IS NOT NULL)) AS `supplyVoltage__both_nonnull`
  , SUM((o.`supplyVoltage` IS NOT NULL AND w.`supplyVoltage` IS NOT NULL AND o.`supplyVoltage`=w.`supplyVoltage`)) AS `supplyVoltage__source_equal`
  , SUM((o.`supplyVoltage` IS NOT NULL AND w.`supplyVoltage` IS NOT NULL AND o.`supplyVoltage`<>w.`supplyVoltage`)) AS `supplyVoltage__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`supplyVoltage` IS NOT NULL)) AS `supplyVoltage__merged_nonnull`
  , SUM((m.`supplyVoltage` IS NOT NULL AND o.`supplyVoltage` IS NOT NULL AND m.`supplyVoltage`=o.`supplyVoltage`)) AS `supplyVoltage__merged_matches_old`
  , SUM((m.`supplyVoltage` IS NOT NULL AND w.`supplyVoltage` IS NOT NULL AND m.`supplyVoltage`=w.`supplyVoltage`)) AS `supplyVoltage__merged_matches_wh`
  , SUM((m.`supplyVoltage` IS NOT NULL AND o.`supplyVoltage` IS NOT NULL AND w.`supplyVoltage` IS NOT NULL AND m.`supplyVoltage`<>o.`supplyVoltage` AND m.`supplyVoltage`<>w.`supplyVoltage`)) AS `supplyVoltage__merged_matches_neither`
  , SUM(o.`txBatteryStatus` IS NOT NULL) AS `txBatteryStatus__old_nonnull`
  , SUM(w.`txBatteryStatus` IS NOT NULL) AS `txBatteryStatus__wh_nonnull`
  , SUM((o.`txBatteryStatus` IS NOT NULL AND w.`txBatteryStatus` IS NOT NULL)) AS `txBatteryStatus__both_nonnull`
  , SUM((o.`txBatteryStatus` IS NOT NULL AND w.`txBatteryStatus` IS NOT NULL AND o.`txBatteryStatus`=w.`txBatteryStatus`)) AS `txBatteryStatus__source_equal`
  , SUM((o.`txBatteryStatus` IS NOT NULL AND w.`txBatteryStatus` IS NOT NULL AND o.`txBatteryStatus`<>w.`txBatteryStatus`)) AS `txBatteryStatus__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`txBatteryStatus` IS NOT NULL)) AS `txBatteryStatus__merged_nonnull`
  , SUM((m.`txBatteryStatus` IS NOT NULL AND o.`txBatteryStatus` IS NOT NULL AND m.`txBatteryStatus`=o.`txBatteryStatus`)) AS `txBatteryStatus__merged_matches_old`
  , SUM((m.`txBatteryStatus` IS NOT NULL AND w.`txBatteryStatus` IS NOT NULL AND m.`txBatteryStatus`=w.`txBatteryStatus`)) AS `txBatteryStatus__merged_matches_wh`
  , SUM((m.`txBatteryStatus` IS NOT NULL AND o.`txBatteryStatus` IS NOT NULL AND w.`txBatteryStatus` IS NOT NULL AND m.`txBatteryStatus`<>o.`txBatteryStatus` AND m.`txBatteryStatus`<>w.`txBatteryStatus`)) AS `txBatteryStatus__merged_matches_neither`
  , SUM(o.`windBatteryStatus` IS NOT NULL) AS `windBatteryStatus__old_nonnull`
  , SUM(w.`windBatteryStatus` IS NOT NULL) AS `windBatteryStatus__wh_nonnull`
  , SUM((o.`windBatteryStatus` IS NOT NULL AND w.`windBatteryStatus` IS NOT NULL)) AS `windBatteryStatus__both_nonnull`
  , SUM((o.`windBatteryStatus` IS NOT NULL AND w.`windBatteryStatus` IS NOT NULL AND o.`windBatteryStatus`=w.`windBatteryStatus`)) AS `windBatteryStatus__source_equal`
  , SUM((o.`windBatteryStatus` IS NOT NULL AND w.`windBatteryStatus` IS NOT NULL AND o.`windBatteryStatus`<>w.`windBatteryStatus`)) AS `windBatteryStatus__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windBatteryStatus` IS NOT NULL)) AS `windBatteryStatus__merged_nonnull`
  , SUM((m.`windBatteryStatus` IS NOT NULL AND o.`windBatteryStatus` IS NOT NULL AND m.`windBatteryStatus`=o.`windBatteryStatus`)) AS `windBatteryStatus__merged_matches_old`
  , SUM((m.`windBatteryStatus` IS NOT NULL AND w.`windBatteryStatus` IS NOT NULL AND m.`windBatteryStatus`=w.`windBatteryStatus`)) AS `windBatteryStatus__merged_matches_wh`
  , SUM((m.`windBatteryStatus` IS NOT NULL AND o.`windBatteryStatus` IS NOT NULL AND w.`windBatteryStatus` IS NOT NULL AND m.`windBatteryStatus`<>o.`windBatteryStatus` AND m.`windBatteryStatus`<>w.`windBatteryStatus`)) AS `windBatteryStatus__merged_matches_neither`
  , SUM(o.`windDir` IS NOT NULL) AS `windDir__old_nonnull`
  , SUM(w.`windDir` IS NOT NULL) AS `windDir__wh_nonnull`
  , SUM((o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL)) AS `windDir__both_nonnull`
  , SUM((o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`=w.`windDir`)) AS `windDir__source_equal`
  , SUM((o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND o.`windDir`<>w.`windDir`)) AS `windDir__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windDir` IS NOT NULL)) AS `windDir__merged_nonnull`
  , SUM((m.`windDir` IS NOT NULL AND o.`windDir` IS NOT NULL AND m.`windDir`=o.`windDir`)) AS `windDir__merged_matches_old`
  , SUM((m.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND m.`windDir`=w.`windDir`)) AS `windDir__merged_matches_wh`
  , SUM((m.`windDir` IS NOT NULL AND o.`windDir` IS NOT NULL AND w.`windDir` IS NOT NULL AND m.`windDir`<>o.`windDir` AND m.`windDir`<>w.`windDir`)) AS `windDir__merged_matches_neither`
  , SUM(o.`windGust` IS NOT NULL) AS `windGust__old_nonnull`
  , SUM(w.`windGust` IS NOT NULL) AS `windGust__wh_nonnull`
  , SUM((o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL)) AS `windGust__both_nonnull`
  , SUM((o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`=w.`windGust`)) AS `windGust__source_equal`
  , SUM((o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND o.`windGust`<>w.`windGust`)) AS `windGust__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windGust` IS NOT NULL)) AS `windGust__merged_nonnull`
  , SUM((m.`windGust` IS NOT NULL AND o.`windGust` IS NOT NULL AND m.`windGust`=o.`windGust`)) AS `windGust__merged_matches_old`
  , SUM((m.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND m.`windGust`=w.`windGust`)) AS `windGust__merged_matches_wh`
  , SUM((m.`windGust` IS NOT NULL AND o.`windGust` IS NOT NULL AND w.`windGust` IS NOT NULL AND m.`windGust`<>o.`windGust` AND m.`windGust`<>w.`windGust`)) AS `windGust__merged_matches_neither`
  , SUM(o.`windGustDir` IS NOT NULL) AS `windGustDir__old_nonnull`
  , SUM(w.`windGustDir` IS NOT NULL) AS `windGustDir__wh_nonnull`
  , SUM((o.`windGustDir` IS NOT NULL AND w.`windGustDir` IS NOT NULL)) AS `windGustDir__both_nonnull`
  , SUM((o.`windGustDir` IS NOT NULL AND w.`windGustDir` IS NOT NULL AND o.`windGustDir`=w.`windGustDir`)) AS `windGustDir__source_equal`
  , SUM((o.`windGustDir` IS NOT NULL AND w.`windGustDir` IS NOT NULL AND o.`windGustDir`<>w.`windGustDir`)) AS `windGustDir__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windGustDir` IS NOT NULL)) AS `windGustDir__merged_nonnull`
  , SUM((m.`windGustDir` IS NOT NULL AND o.`windGustDir` IS NOT NULL AND m.`windGustDir`=o.`windGustDir`)) AS `windGustDir__merged_matches_old`
  , SUM((m.`windGustDir` IS NOT NULL AND w.`windGustDir` IS NOT NULL AND m.`windGustDir`=w.`windGustDir`)) AS `windGustDir__merged_matches_wh`
  , SUM((m.`windGustDir` IS NOT NULL AND o.`windGustDir` IS NOT NULL AND w.`windGustDir` IS NOT NULL AND m.`windGustDir`<>o.`windGustDir` AND m.`windGustDir`<>w.`windGustDir`)) AS `windGustDir__merged_matches_neither`
  , SUM(o.`windSpeed` IS NOT NULL) AS `windSpeed__old_nonnull`
  , SUM(w.`windSpeed` IS NOT NULL) AS `windSpeed__wh_nonnull`
  , SUM((o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL)) AS `windSpeed__both_nonnull`
  , SUM((o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`=w.`windSpeed`)) AS `windSpeed__source_equal`
  , SUM((o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND o.`windSpeed`<>w.`windSpeed`)) AS `windSpeed__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windSpeed` IS NOT NULL)) AS `windSpeed__merged_nonnull`
  , SUM((m.`windSpeed` IS NOT NULL AND o.`windSpeed` IS NOT NULL AND m.`windSpeed`=o.`windSpeed`)) AS `windSpeed__merged_matches_old`
  , SUM((m.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND m.`windSpeed`=w.`windSpeed`)) AS `windSpeed__merged_matches_wh`
  , SUM((m.`windSpeed` IS NOT NULL AND o.`windSpeed` IS NOT NULL AND w.`windSpeed` IS NOT NULL AND m.`windSpeed`<>o.`windSpeed` AND m.`windSpeed`<>w.`windSpeed`)) AS `windSpeed__merged_matches_neither`
  , SUM(o.`windchill` IS NOT NULL) AS `windchill__old_nonnull`
  , SUM(w.`windchill` IS NOT NULL) AS `windchill__wh_nonnull`
  , SUM((o.`windchill` IS NOT NULL AND w.`windchill` IS NOT NULL)) AS `windchill__both_nonnull`
  , SUM((o.`windchill` IS NOT NULL AND w.`windchill` IS NOT NULL AND o.`windchill`=w.`windchill`)) AS `windchill__source_equal`
  , SUM((o.`windchill` IS NOT NULL AND w.`windchill` IS NOT NULL AND o.`windchill`<>w.`windchill`)) AS `windchill__source_conflict`
  , SUM((m.dateTime IS NOT NULL AND m.`windchill` IS NOT NULL)) AS `windchill__merged_nonnull`
  , SUM((m.`windchill` IS NOT NULL AND o.`windchill` IS NOT NULL AND m.`windchill`=o.`windchill`)) AS `windchill__merged_matches_old`
  , SUM((m.`windchill` IS NOT NULL AND w.`windchill` IS NOT NULL AND m.`windchill`=w.`windchill`)) AS `windchill__merged_matches_wh`
  , SUM((m.`windchill` IS NOT NULL AND o.`windchill` IS NOT NULL AND w.`windchill` IS NOT NULL AND m.`windchill`<>o.`windchill` AND m.`windchill`<>w.`windchill`)) AS `windchill__merged_matches_neither`
FROM `old_weewx`.`archive` o
JOIN `weewx_WH1080`.`archive` w ON w.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` m ON m.dateTime=o.dateTime
WHERE o.dateTime >= 1388534400 AND o.dateTime < 1420070400;
