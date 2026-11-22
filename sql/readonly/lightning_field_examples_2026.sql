-- Three representative earliest target rows; aggregate review only, no mutation.
SELECT dateTime, lightning_disturber_count, lightning_strike_count, lightning_noise_count
FROM loucka_reconstruction.archive
WHERE dateTime>=1767225600 AND dateTime<1798761600
  AND lightning_disturber_count IS NOT NULL
ORDER BY dateTime ASC
LIMIT 3;
