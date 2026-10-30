-- MASTER_QC_READONLY.sql
-- Počasí Loučka — samostatné diagnostické SELECTy pro MASTER_AUDIT.
-- Verze 2026-10-30. Každý blok je read-only; nic nevkládat ani neopravovat.
-- Databáze loucka_reconstruction; názvy všech šesti schémat vždy escapovat.
-- Archivní dateTime = konec intervalu v UTC; lokální dny mají hranice (start,end].
-- SQL session FROM_UNIXTIME() závisí na systémové zóně; pro právně/meteorologicky
-- přesné měsíce používat předpočítané epoch hranice Europe/Prague.
-- Při max_statement_time dotazy dělit po měsících.

START TRANSACTION READ ONLY;

-- Q01 Inventář pracovní DB a 3 záloh Fáze A.
SELECT
  (SELECT COUNT(*) FROM `loucka_reconstruction`.archive) AS archive_n,
  (SELECT COUNT(*) FROM `loucka_reconstruction`.rain_daily_reset_backup_2009_2011_v1) AS backup_resets_328,
  (SELECT COUNT(*) FROM `loucka_reconstruction`.rain_phase_a_201006_backup_20261030_v1) AS backup_june_30,
  (SELECT COUNT(*) FROM `loucka_reconstruction`.rain_phase_a_backup_20261030_v1) AS backup_isolated_2,
  (SELECT COUNT(*) FROM `loucka_reconstruction`.wh1080_missing_5min_candidates_20261030) AS staging_49796;

-- Q02 Audit applied (pouze existující opravy, nic nesimulovat).
SELECT batch_key,variable,state,COUNT(*) AS n,
       ROUND(SUM(CASE WHEN variable='rain' THEN old_value-new_value ELSE 0 END)*10,3) AS removed_rain_mm
FROM `loucka_reconstruction`.reconstruction_changes
WHERE batch_key IN (
 'rain-2009-2011-utc-midnight-reset-v1',
 'rain-phaseA-june2010-corrected-20261030-v1',
 'rain-phaseA-apply-20261030-v1',
 'rainrate-restore-2009-2025-v1'
)
GROUP BY batch_key,variable,state ORDER BY batch_key,variable,state;

-- Q03 Zálohované srážky současně odpovídají aplikovanému stavu?
SELECT 'UTC-reset-2009-2011' AS group_name,COUNT(*) n, SUM(a.rain=0) current_zero,
       ROUND(SUM(b.rain_before)*10,3) old_mm
FROM `loucka_reconstruction`.rain_daily_reset_backup_2009_2011_v1 b
JOIN `loucka_reconstruction`.archive a USING(dateTime)
UNION ALL
SELECT 'June-2010',COUNT(*),SUM(a.rain=0),ROUND(SUM(b.rain_before)*10,3)
FROM `loucka_reconstruction`.rain_phase_a_201006_backup_20261030_v1 b
JOIN `loucka_reconstruction`.archive a USING(dateTime)
UNION ALL
SELECT 'isolated-2011-2025',COUNT(*),SUM(a.rain=0),ROUND(SUM(b.rain_before)*10,3)
FROM `loucka_reconstruction`.rain_phase_a_backup_20261030_v1 b
JOIN `loucka_reconstruction`.archive a USING(dateTime);

-- Q04 Červenec 2021 podle místních hranic CEST a (start,end].
SELECT COUNT(*) archive_rows,ROUND(SUM(rain)*10,4) july2021_mm,COUNT(rain) known
FROM `loucka_reconstruction`.archive
WHERE dateTime > 1625090400 AND dateTime <= 1627768800;

-- Q05 Distribuce WH1080 staging, bez kolize. Žádný INSERT do archive.
SELECT c.status,COUNT(*) n,SUM(a.dateTime IS NOT NULL) existing_targets,
       SUM(c.source_time<>c.target_time) time_shifted
FROM `loucka_reconstruction`.wh1080_missing_5min_candidates_20261030 c
LEFT JOIN `loucka_reconstruction`.archive a ON a.dateTime=c.target_time
GROUP BY c.status;

-- Q06 Kontrola numerické sémantiky větru v kandidátech.
-- V roce 2011 očekáváme poměr 1, po roce 2013 m/s=>km/h 3,6.
SELECT YEAR(FROM_UNIXTIME(c.source_time)) AS local_year,
 COUNT(*) n, ROUND(AVG(c.windSpeed_kmh/w.windSpeed),5) avg_ratio,
 ROUND(MIN(c.windSpeed_kmh/w.windSpeed),5) min_ratio,
 ROUND(MAX(c.windSpeed_kmh/w.windSpeed),5) max_ratio
FROM `loucka_reconstruction`.wh1080_missing_5min_candidates_20261030 c
JOIN `weewx_WH1080`.archive w ON w.dateTime=c.source_time
WHERE ((c.source_time>=1293840000 AND c.source_time<1325376000)
    OR (c.source_time>=1546300800 AND c.source_time<1609459200))
  AND w.windSpeed>0
GROUP BY local_year ORDER BY local_year;

-- Q07 Duben 2022 diagnostika Td (UTC kalendář, diagnóza, NE aplikace).
SELECT COUNT(*) compared,
       SUM(delta_c > 2) AS inconsistent_gt2c,
       ROUND(MAX(delta_c),2) AS max_delta_c
FROM (
 SELECT ABS(dewpoint-(243.04*(LN(outHumidity/100)+17.625*outTemp/(243.04+outTemp))/
        (17.625-(LN(outHumidity/100)+17.625*outTemp/(243.04+outTemp))))) delta_c
 FROM `loucka_reconstruction`.archive
 WHERE dateTime > 1648771200 AND dateTime <= 1651363200
 AND outHumidity BETWEEN 1 AND 100 AND outTemp BETWEEN -50 AND 60
 AND dewpoint IS NOT NULL
) t;

-- Q08 Pouze podezřelé nenulové GW špičky rainRate, v rekonstrukci 0.
SELECT YEAR(FROM_UNIXTIME(r.dateTime)) local_year,
 COUNT(*) n, ROUND(MAX(g.rainRate)*10,2) max_source_mmh
FROM `loucka_reconstruction`.archive r
JOIN `pocasi-loucka.eu_GW1000`.archive g USING(dateTime)
WHERE r.dateTime>=1672531200 AND r.dateTime<1735689600
  AND g.rainRate>5 AND r.rainRate=0
GROUP BY local_year;

-- Q09 Systematické produkční nuly intensity: omezit na jeden rok.
SELECT COUNT(*) common_rows,
 SUM(p.rainRate=0 AND g.rainRate>0) AS production_zero_gw_positive,
 SUM(p.rainRate>0 AND g.rainRate=0) AS reverse_case
FROM `pocasi-loucka.eu`.archive p
JOIN `pocasi-loucka.eu_GW1000`.archive g USING(dateTime)
WHERE p.dateTime>=1704067200 AND p.dateTime<1735689600;

-- Q10 Květen 2026 — jen dvě konkrétní původní zdrojové anomálie.
SELECT r.dateTime,FROM_UNIXTIME(r.dateTime) AS local_end_time,
 ROUND(r.rain*10,3) AS reconstructed_mm,
 ROUND(g.rain*10,3) AS original_gw_mm
FROM `loucka_reconstruction`.archive r
JOIN `pocasi-loucka.eu_GW1000`.archive g USING(dateTime)
-- Pevné UTC epochy; zdrojové incidenty byly 06:35 a 23:15 Europe/Prague (CEST).
-- Není závislé na @@session.time_zone ani na DB timezone tabulkách.
WHERE r.dateTime IN (1778560500,1778966100);

-- Q11 Párové tlakové rozdíly, srpen 2026 (UTC, report má i místní souhrny).
SELECT COUNT(*) n,
 ROUND(AVG(r.barometer-g.barometer),3) barometer_mean_delta_hpa,
 ROUND(AVG(r.pressure-g.pressure),3) pressure_mean_delta_hpa
FROM `loucka_reconstruction`.archive r
JOIN `pocasi-loucka.eu_GW1000`.archive g USING(dateTime)
WHERE r.dateTime>1785544800 AND r.dateTime<=1788223200;

-- Q12 PM2.5 saturace září-říjen 2024 (UTC).
SELECT COUNT(*) n,SUM(pm25_1>=999.8) AS saturated_999_8,
       SUM(pm25_1>500) AS over500
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1725148800 AND dateTime<1730419200;

-- Q13 Suspektní názvy bleskových polí. Shoda je ztráta informace.
SELECT COUNT(lightning_noise_count) n_noise,
       SUM(lightning_noise_count=lightning_strike_count) n_equals_strikes,
       MIN(lightning_disturber_count) min_disturber,
       MAX(lightning_disturber_count) max_disturber
FROM `pocasi-loucka.eu`.archive
WHERE dateTime>=1778500000 AND lightning_noise_count IS NOT NULL;

-- Q14 Před vlastním schválením konkrétního kandidáta vyžadovat
-- NULL-safe původní hodnotu, bez jakéhokoli zápisu:
-- SELECT dateTime,rain,rainRate,usUnits,`interval`
-- FROM `loucka_reconstruction`.archive
-- WHERE dateTime=:approved_target_time AND rain <=> :expected_old_rain;

COMMIT;
