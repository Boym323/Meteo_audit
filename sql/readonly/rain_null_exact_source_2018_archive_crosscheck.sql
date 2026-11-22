-- SELECT-only alternate archive exact-time cross-check for Q1 2018 rain NULLs.
SELECT UTC_TIMESTAMP() AS query_time_utc,COUNT(*) AS recon_rain_null_rows,
 SUM(p.dateTime IS NOT NULL) prod_exact_rows,SUM(p.rain IS NOT NULL) prod_rain_available,
 SUM(p.rain=0) prod_rain_zero,SUM(p.rain>0) prod_rain_positive,
 SUM(g.dateTime IS NOT NULL) gw_exact_rows,SUM(g.rain IS NOT NULL) gw_rain_available,
 SUM(g.rain=0) gw_rain_zero,SUM(g.rain>0) gw_rain_positive,
 SUM(o.dateTime IS NOT NULL) old_exact_rows,SUM(o.rain IS NOT NULL) old_rain_available,
 SUM(o.rain=0) old_rain_zero,SUM(o.rain>0) old_rain_positive,
 SUM(w.dateTime IS NOT NULL) wh_exact_rows,SUM(w.rain IS NOT NULL) wh_rain_available,
 SUM(w.rain=0) wh_rain_zero,SUM(w.rain>0) wh_rain_positive,
 SUM(po.dateTime IS NOT NULL) oldprod_exact_rows,SUM(po.rain IS NOT NULL) oldprod_rain_available,
 SUM(r.rainRate IS NULL) recon_rate_null,SUM(r.rainRate=0) recon_rate_zero,SUM(r.rainRate>0) recon_rate_positive
FROM loucka_reconstruction.archive r
LEFT JOIN `pocasi-loucka.eu`.archive p ON p.dateTime=r.dateTime
LEFT JOIN `pocasi-loucka.eu_GW1000`.archive g ON g.dateTime=r.dateTime
LEFT JOIN old_weewx.archive o ON o.dateTime=r.dateTime
LEFT JOIN weewx_WH1080.archive w ON w.dateTime=r.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.archive po ON po.dateTime=r.dateTime
WHERE r.dateTime>=1514764800 AND r.dateTime<1522540800 AND r.rain IS NULL;
