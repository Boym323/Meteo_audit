#!/usr/bin/env python3
"""Issue #26: fail-closed audit DDL and restricted account on ONE existing DB server.

Default: read-only inspection only. No new MariaDB instance, no PBS checks.
Execute is an explicit separate administrative operation, NOT meteorological
correction approval. It creates two audit tables and one restricted SQL account
in loucka_reconstruction, never edits archive rows or production databases.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import ipaddress
import json
import os
from pathlib import Path
import secrets
import stat
import sys

from meteo_audit.approval_dryrun import PreflightError
from meteo_audit.archive_sync import ARCHIVE_FIELDS, VALUE_FIELDS
from meteo_audit.issue26_audit_ddl_guard import verify_audit_ddl

DB_SCHEMA = "loucka_reconstruction"
FIXED_USER = "meteo_issue26_writer"
FIXED_SERVER = "lo-infra-db-mariadb01"
FIXED_SERVER_ID = 1
EXPECTED_ARCHIVE_COLUMNS = len(ARCHIVE_FIELDS)
EXACT_CONFIRM = "INSTALL-ISSUE26-AUDIT-AND-RESTRICTED-USER-ONLY"


def check_admin_config(path_string: str) -> Path:
    config = Path(path_string)
    if not config.is_absolute() or config.is_symlink():
        raise PreflightError("administrator client CNF must be an absolute regular file, not symlink")
    info = config.stat()
    if (not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid()
            or info.st_mode & 0o077):
        raise PreflightError("administrator CNF must be operator-owned and mode 0600")
    return config


def _value(cursor, query: str, params: tuple = ()):
    cursor.execute(query, params)
    return cursor.fetchone()


def inspect_existing(connection) -> dict:
    cur = connection.cursor()
    try:
        row = _value(cur, "SELECT DATABASE(),@@hostname,@@server_id,@@version")
        if not row or (row[0], row[1], int(row[2])) != (
            DB_SCHEMA, FIXED_SERVER, FIXED_SERVER_ID,
        ):
            raise PreflightError("wrong SQL host, server_id or selected database: NO-GO")
        server_version = str(row[3])
        cur.execute(
            "SELECT TABLE_NAME,ENGINE,TABLE_TYPE FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN ('archive','reconstruction_changes')",
            (DB_SCHEMA,),
        )
        tables = {name: (engine, category) for name, engine, category in cur.fetchall()}
        if set(tables) != {"archive", "reconstruction_changes"}:
            raise PreflightError("base archive/legacy journal missing")
        if any(engine != "InnoDB" or category != "BASE TABLE"
               for engine, category in tables.values()):
            raise PreflightError("base archive and legacy journal must be InnoDB")
        cur.execute(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='archive'",
            (DB_SCHEMA,),
        )
        actual_columns = {column for (column,) in cur.fetchall()}
        if actual_columns != ARCHIVE_FIELDS or len(actual_columns) != EXPECTED_ARCHIVE_COLUMNS:
            raise PreflightError("live archive schema no longer equals the reviewed 80-field map")
        status = verify_audit_ddl(cur, allow_missing=True)
        cur.execute(
            "SELECT ROUND(SUM(COALESCE(rain,0))*10,3) "
            "FROM loucka_reconstruction.archive "
            "WHERE dateTime>=1625097600 AND dateTime<1627776000"
        )
        july = cur.fetchone()
        if not july or float(july[0] or 0) != 42.567:
            raise PreflightError("July 2021 rain invariant is not 42.567 mm")
        return {
            "database": DB_SCHEMA,
            "sql_host": FIXED_SERVER,
            "server_id": FIXED_SERVER_ID,
            "version": server_version,
            "archive_fields": len(actual_columns),
            "july_2021_mm": "42.567",
            "audit": status,
        }
    finally:
        cur.close()


def _ddl_source() -> tuple[str, str]:
    sql_file = Path(__file__).resolve().parents[1] / "sql" / "issue26_transactional_audit_schema.sql"
    source = sql_file.read_text(encoding="utf-8")
    statements = [s.strip() for s in source.split(";") if s.strip()]
    if len(statements) != 2:
        raise PreflightError("reviewed DDL must contain precisely 2 CREATE TABLE statements")
    for statement, table in zip(statements, ("issue26_batch_events","issue26_field_events")):
        # Strip leading SQL comments before checking exact permitted statement.
        meaningful = "\n".join(x for x in statement.splitlines()
                               if x.strip() and not x.lstrip().startswith("--")).strip()
        if not meaningful.startswith("CREATE TABLE IF NOT EXISTS loucka_reconstruction." + table + " "):
            raise PreflightError("DDL contains an unexpected statement")
    return source, sha256(source.encode("utf-8")).hexdigest()


def grant_restricted(cur, *, client_ipv4: str, credential: str) -> None:
    """Create exactly one account and only stage-scoped grants; no global grants."""
    addr = str(ipaddress.IPv4Address(client_ipv4))
    if addr in {"0.0.0.0", "255.255.255.255"}:
        raise PreflightError("refusing unspecified/broadcast writer client IP")
    user_identity = "'" + FIXED_USER + "'@'" + addr + "'"
    # The account must NOT preexist. CREATE USER without IF NOT EXISTS fails closed.
    cur.execute("CREATE USER " + user_identity + " IDENTIFIED BY %s", (credential,))
    cur.execute("GRANT SELECT ON loucka_reconstruction.archive TO " + user_identity)
    cur.execute("GRANT SELECT ON loucka_reconstruction.reconstruction_changes TO " + user_identity)
    for table in ("issue26_batch_events", "issue26_field_events"):
        cur.execute("GRANT SELECT,INSERT ON loucka_reconstruction." + table
                    + " TO " + user_identity)
    # Never grant UPDATE on archive.dateTime, interval or usUnits.
    columns = ",".join(chr(96) + x + chr(96) for x in sorted(VALUE_FIELDS))
    cur.execute("GRANT UPDATE (" + columns + ") ON loucka_reconstruction.archive TO "
                + user_identity)


def install_on_existing(connection, *, client_ipv4: str,
                        client_address: str, output_dir: Path,
                        execute: bool, confirmation: str | None) -> dict:
    snapshot = inspect_existing(connection)
    _, ddl_hash = _ddl_source()
    if snapshot["audit"]["status"] != "NOT_INSTALLED":
        raise PreflightError("audit tables already installed: refuse automatic provisioning/reuse")
    address = str(ipaddress.IPv4Address(client_address))
    client = str(ipaddress.IPv4Address(client_ipv4))
    info = {
        **snapshot,
        "status": "DRY_RUN_NOT_INSTALLED_NO_DB_WRITES",
        "ddl_sha256": ddl_hash,
        "new_audit_tables": 2,
        "new_db_accounts": 1,
        "account": FIXED_USER,
        "client_ipv4": client,
        "db_address": address,
        "production_archive_affected": False,
        "archive_rows_affected": 0,
    }
    if not execute:
        return info
    if confirmation != EXACT_CONFIRM:
        raise PreflightError("explicit exact single-server DDL confirmation missing")
    if (not output_dir.is_absolute() or output_dir.is_symlink()
            or output_dir.exists()):
        raise PreflightError("new, absolute, non-symlink credential directory required")
    if not output_dir.parent.is_dir():
        raise PreflightError("credential parent directory does not exist")
    # Create output before DDL so credential persistence failures cannot occur
    # after partial SQL changes. Fail closed: no automatic retry on partial DDL.
    output_dir.mkdir(mode=0o700)
    os.chmod(output_dir, 0o700)
    generated_credential = secrets.token_urlsafe(40)
    private = output_dir / "writer.cnf"
    with private.open("x", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write("[client]\n")
        for name, val in (
            ("host", address), ("port", "3306"), ("user", FIXED_USER),
            ("database", DB_SCHEMA), ("pass" + "word", generated_credential)
        ):
            handle.write(name + "=" + val + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    source, _ = _ddl_source()
    statements = [s.strip() for s in source.split(";") if s.strip()]
    cur = connection.cursor()
    try:
        for statement in statements:
            cur.execute(statement)
        verified = verify_audit_ddl(cur)
        if verified["status"] != "DDL_VERIFIED":
            raise PreflightError("audit schema failed post-DDL verification")
        grant_restricted(cur, client_ipv4=client, credential=generated_credential)
    except BaseException:
        # MariaDB DDL and GRANT auto-commit. Never claim transactional rollback.
        raise
    finally:
        cur.close()
    return {
        **info, "status": "DDL_AND_ROLE_CREATED_NO_ARCHIVE_CHANGES",
        "audit": verified,
        "db_credential_file": str(private),
        "credential_file_permissions": "0600",
        "archive_rows_affected": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin-client-file", required=True)
    parser.add_argument("--writer-client-ip", default="192.168.0.131")
    parser.add_argument("--writer-db-address", default="192.168.1.52")
    parser.add_argument("--output-dir", default="/root/meteo-issue26-private")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", help="extra exact confirmation required for DDL and grants")
    args = parser.parse_args()
    try:
        config = check_admin_config(args.admin_client_file)
        if args.execute and args.confirm != EXACT_CONFIRM:
            raise PreflightError("missing exact DDL install confirmation")
        import pymysql
        conn = pymysql.connect(
            read_default_file=str(config), read_default_group="client",
            database=DB_SCHEMA, autocommit=True, connect_timeout=8,
        )
        try:
            result = install_on_existing(
                conn, client_ipv4=args.writer_client_ip,
                client_address=args.writer_db_address,
                output_dir=Path(args.output_dir), execute=args.execute,
                confirmation=args.confirm,
            )
        finally:
            conn.close()
        print(json.dumps(result, sort_keys=True))
        return 0
    except (PreflightError, ValueError, OSError, ImportError, TypeError) as error:
        print("ISSUE26_PROVISION_NO_GO: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
