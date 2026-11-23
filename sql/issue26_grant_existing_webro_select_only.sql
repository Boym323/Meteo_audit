-- Issue 26: allow the EXISTING loucka_web_ro account to perform
-- read-only review of ONLY FOUR reconstruction tables.
-- RUN MANUALLY in Navicat as an existing administrator, once.
-- This DOES NOT CREATE a user, change a password, modify data,
-- change production privileges or authorize an issue26 APPLY.
-- Do not run if existing account is not exactly as inspected.
--
-- Read-only inspection BEFORE GRANT:
SELECT User,Host FROM mysql.user
 WHERE User='loucka_web_ro'
 ORDER BY Host;
SHOW GRANTS FOR 'loucka_web_ro'@'192.168.0.131';
SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES
 WHERE TABLE_SCHEMA='loucka_reconstruction'
   AND TABLE_NAME IN (
     'archive','reconstruction_changes',
     'issue26_batch_events','issue26_field_events'
   )
 ORDER BY TABLE_NAME;

-- Apply only to the already-existing exact user@host.
-- No schema-wide SELECT privilege, no INSERT, UPDATE or DELETE.
GRANT SELECT ON loucka_reconstruction.archive
 TO 'loucka_web_ro'@'192.168.0.131';

GRANT SELECT ON loucka_reconstruction.reconstruction_changes
 TO 'loucka_web_ro'@'192.168.0.131';

GRANT SELECT ON loucka_reconstruction.issue26_batch_events
 TO 'loucka_web_ro'@'192.168.0.131';

GRANT SELECT ON loucka_reconstruction.issue26_field_events
 TO 'loucka_web_ro'@'192.168.0.131';

-- Verify (read-only): exact four TABLE SELECT grants.
SHOW GRANTS FOR 'loucka_web_ro'@'192.168.0.131';
