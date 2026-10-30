-- ADMINISTRATOR RUNBOOK ONLY. Never run from the audit application.
-- Use the narrowest client host pattern approved by the DB administrator.
-- Replace <approved-client-host> and enter a generated password from the
-- administrator's secret manager directly in the protected admin session.
-- Do not store a filled-in copy in this repository or a shell history.
CREATE USER 'meteo_audit_ro'@'<approved-client-host>' IDENTIFIED BY '<set-out-of-band>';
GRANT SELECT ON `pocasi-loucka.eu`.`archive` TO 'meteo_audit_ro'@'<approved-client-host>';
GRANT SELECT ON `loucka_reconstruction`.`archive` TO 'meteo_audit_ro'@'<approved-client-host>';
GRANT SELECT ON `pocasi-loucka.eu_GW1000`.`archive` TO 'meteo_audit_ro'@'<approved-client-host>';
GRANT SELECT ON `pocasi-loucka.eu_old`.`archive` TO 'meteo_audit_ro'@'<approved-client-host>';
GRANT SELECT ON `old_weewx`.`archive` TO 'meteo_audit_ro'@'<approved-client-host>';
GRANT SELECT ON `weewx_WH1080`.`archive` TO 'meteo_audit_ro'@'<approved-client-host>';

-- Verify effective grants and connection identity after setup. These are read-only.
SHOW GRANTS FOR 'meteo_audit_ro'@'<approved-client-host>';
SELECT CURRENT_USER(), CURRENT_ROLE();
-- Expected data privileges: SELECT on the six archive tables above only.
-- If global/role grants permit writes, remove them in the admin process before use.
