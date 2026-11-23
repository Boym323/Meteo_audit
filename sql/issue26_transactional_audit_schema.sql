-- Issue #26 schema proposal. NEVER run against production.
-- DDL deployment is a distinct owner-reviewed operation. CI uses synthetic data.
CREATE TABLE IF NOT EXISTS loucka_reconstruction.issue26_batch_events (
  batch_id varchar(80) NOT NULL,
  event_type enum('APPLY','ROLLBACK') NOT NULL,
  payload_sha256 char(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  before_image_sha256 char(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  approval_mac_sha256 char(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  approver varchar(120) NOT NULL,
  operation_count int unsigned NOT NULL,
  event_time timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (batch_id,event_type)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS loucka_reconstruction.issue26_field_events (
  id bigint unsigned NOT NULL AUTO_INCREMENT,
  batch_id varchar(80) NOT NULL,
  event_type enum('APPLY','ROLLBACK') NOT NULL,
  target_time bigint NOT NULL,
  variable varchar(64) NOT NULL,
  old_value double NULL,
  new_value double NULL,
  source_ref varchar(255) NOT NULL,
  unit_epoch_ref varchar(255) NOT NULL,
  rule_version varchar(120) NOT NULL,
  diagnosis_confidence varchar(16) NOT NULL,
  replacement_confidence varchar(16) NOT NULL,
  event_time timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (id),
  UNIQUE KEY uniq_issue26_batch_action_target
      (batch_id,event_type,target_time,variable),
  KEY idx_issue26_target_variable (target_time,variable),
  CONSTRAINT fk_issue26_batch_event FOREIGN KEY (batch_id,event_type)
    REFERENCES loucka_reconstruction.issue26_batch_events
      (batch_id,event_type)
) ENGINE=InnoDB;
