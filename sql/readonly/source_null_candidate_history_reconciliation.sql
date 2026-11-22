-- SELECT-only: exact-time source values for current NULL targets, checked against
-- latest recorded reconstruction history. Run by year if the statement limit is hit.
WITH source_candidates AS (
  SELECT s.dateTime AS target_time,'outTemp' AS variable
  FROM old_weewx.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.outTemp IS NOT NULL AND r.outTemp IS NULL
  UNION
  SELECT s.dateTime,'outTemp' FROM weewx_WH1080.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.outTemp IS NOT NULL AND r.outTemp IS NULL
  UNION
  SELECT s.dateTime,'outHumidity' FROM old_weewx.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.outHumidity IS NOT NULL AND r.outHumidity IS NULL
  UNION
  SELECT s.dateTime,'outHumidity' FROM weewx_WH1080.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.outHumidity IS NOT NULL AND r.outHumidity IS NULL
  UNION
  SELECT s.dateTime,'rain' FROM old_weewx.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.rain IS NOT NULL AND r.rain IS NULL
  UNION
  SELECT s.dateTime,'rain' FROM weewx_WH1080.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.rain IS NOT NULL AND r.rain IS NULL
  UNION
  SELECT s.dateTime,'rainRate' FROM old_weewx.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.rainRate IS NOT NULL AND r.rainRate IS NULL
  UNION
  SELECT s.dateTime,'rainRate' FROM weewx_WH1080.archive s JOIN loucka_reconstruction.archive r ON r.dateTime=s.dateTime
  WHERE s.dateTime>=:utc_year_start AND s.dateTime<:utc_year_end
    AND s.rainRate IS NOT NULL AND r.rainRate IS NULL
), ranked_history AS (
  SELECT id,target_time,variable,batch_key,reason,state,old_value,new_value,created_at,
         ROW_NUMBER() OVER(PARTITION BY target_time,variable ORDER BY created_at DESC,id DESC) AS rn
  FROM loucka_reconstruction.reconstruction_changes
  WHERE target_time>=:utc_year_start AND target_time<:utc_year_end
    AND variable IN ('outTemp','outHumidity','rain','rainRate')
)
SELECT c.variable,h.state AS latest_recorded_state,(h.new_value IS NULL) AS latest_new_is_null,
       COUNT(*) AS candidate_targets,COUNT(DISTINCT h.batch_key) AS distinct_batches
FROM source_candidates c
LEFT JOIN ranked_history h ON h.target_time=c.target_time AND h.variable=c.variable AND h.rn=1
GROUP BY c.variable,h.state,(h.new_value IS NULL)
ORDER BY c.variable,h.state,latest_new_is_null;
