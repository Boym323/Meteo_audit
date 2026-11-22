-- Bounded 2026 semantic screen for lightning counters; aggregate output only.
SELECT COUNT(*) AS rows_n,
       SUM(lightning_disturber_count IS NOT NULL) AS disturber_nonnull,
       SUM(lightning_disturber_count BETWEEN 1767225600 AND 1798761600) AS disturber_within_2026_epoch_range,
       SUM(lightning_disturber_count=dateTime) AS disturber_equals_target_epoch,
       MIN(lightning_disturber_count-dateTime) AS disturber_minus_target_min_seconds,
       MAX(lightning_disturber_count-dateTime) AS disturber_minus_target_max_seconds,
       SUM(lightning_disturber_count=lightning_strike_count) AS disturber_equals_strike,
       COUNT(DISTINCT lightning_disturber_count) AS disturber_distinct_values,
       SUM(lightning_noise_count IS NOT NULL) AS noise_nonnull,
       SUM(lightning_noise_count=lightning_strike_count) AS noise_equals_strike
FROM loucka_reconstruction.archive
WHERE dateTime >= 1767225600 AND dateTime < 1798761600;
