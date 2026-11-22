-- SELECT-only DB/session timezone and DST diagnostics.
SELECT @@session.time_zone AS session_time_zone,
       @@global.time_zone AS global_time_zone,
       @@system_time_zone AS system_time_zone,
       NOW() AS session_now,
       UTC_TIMESTAMP() AS utc_now,
       UNIX_TIMESTAMP(NOW()) AS session_now_epoch,
       UNIX_TIMESTAMP(UTC_TIMESTAMP()) AS utc_datetime_interpreted_in_session_epoch,
       TIMESTAMPDIFF(SECOND,NOW(),UTC_TIMESTAMP()) AS session_minus_utc_seconds;

-- Unix epoch to system-local display and round-trip at one summer / one winter point.
SELECT FROM_UNIXTIME(1313438700) AS summer_epoch_local,
       UNIX_TIMESTAMP('2011-08-15 22:05:00') AS summer_roundtrip_epoch,
       FROM_UNIXTIME(1483966800) AS winter_epoch_local,
       UNIX_TIMESTAMP('2017-01-09 14:00:00') AS winter_roundtrip_epoch;

-- DST boundaries in the system timezone: spring skips 02:00-02:59,
-- autumn repeats the 02:00 hour. All inputs are UTC Unix epochs.
SELECT FROM_UNIXTIME(1301187599) AS spring_before,
       FROM_UNIXTIME(1301187600) AS spring_after,
       FROM_UNIXTIME(1319936399) AS autumn_before,
       FROM_UNIXTIME(1319936400) AS autumn_after;

-- Named-zone conversion is separately probed; NULL indicates unavailable zone tables.
SELECT CONVERT_TZ('2011-08-15 22:05:00','Europe/Prague','UTC') AS named_zone_summer,
       CONVERT_TZ('2017-01-09 14:00:00','Europe/Prague','UTC') AS named_zone_winter,
       CONVERT_TZ(FROM_UNIXTIME(1301187600),'SYSTEM','UTC') AS system_to_utc;
