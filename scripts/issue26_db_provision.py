#!/usr/bin/env python3
"""Issue #26: EXISTING-ACCOUNTS-ONLY read-only audit status.

Owner decision (2026-11-23): never create any new MariaDB user account.
The old --execute provisioning path is permanently retired. This command
cannot create users, grants, tables or any data changes on any server.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys

from meteo_audit.approval_dryrun import PreflightError
from meteo_audit.archive_sync import ARCHIVE_FIELDS
from meteo_audit.issue26_audit_ddl_guard import verify_audit_ddl

DB_SCHEMA = "loucka_reconstruction"
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


def check_local_root_socket(name: str) -> Path:
    """Existing database host only: Linux root via local MariaDB Unix socket."""
    if os.geteuid() != 0:
        raise PreflightError("local MariaDB admin socket requires Linux root")
    p = Path(name)
    # No remote socket forwarding or arbitrary socket paths for DDL.
    if str(p) != "/run/mysqld/mysqld.sock" or p.is_symlink():
        raise PreflightError("expected exact MariaDB local socket path")
    info = p.stat()
    if not stat.S_ISSOCK(info.st_mode):
        raise PreflightError("MariaDB Unix socket is missing or not a socket")
    return p


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


def install_on_existing(connection, *, client_ipv4: str,
                        client_address: str, output_dir: Path,
                        execute: bool, confirmation: str | None) -> dict:
    """Legacy-compatible interface, now strictly inspection only.

    All write/provisioning operations are forbidden regardless of confirm.
    No SQL DDL/GRANT/CREATE USER can be reached via this function.
    """
    if execute:
        raise PreflightError(
            "owner policy: NO NEW SQL ACCOUNTS; old DDL/account installer retired"
        )
    snapshot = inspect_existing(connection)
    _, ddl_hash = _ddl_source()
    return {
        **snapshot,
        "status": (
            "EXISTING_AUDIT_DDL_VERIFIED_NO_DB_WRITES"
            if snapshot["audit"]["status"] == "DDL_VERIFIED"
            else "AUDIT_DDL_MISSING_READ_ONLY"
        ),
        "ddl_sha256": ddl_hash,
        "new_audit_tables": 0,
        "new_db_accounts": 0,
        "existing_accounts_only": True,
        "db_writes": 0,
        "production_archive_affected": False,
        "archive_rows_affected": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    db_auth = parser.add_mutually_exclusive_group(required=True)
    db_auth.add_argument("--admin-client-file")
    db_auth.add_argument("--local-root-socket")
    parser.add_argument("--writer-client-ip", default="192.168.0.131")
    parser.add_argument("--writer-db-address", default="192.168.1.52")
    parser.add_argument("--output-dir", default="/root/meteo-issue26-private")
    parser.add_argument("--execute", action="store_true", help="retired: always NO-GO")
    parser.add_argument("--confirm", help="retired: does not enable any writes")
    args = parser.parse_args()
    try:
        if args.execute:
            raise PreflightError(
                "owner policy: NO NEW SQL ACCOUNTS; old --execute installer retired"
            )
        if args.local_root_socket:
            socket = check_local_root_socket(args.local_root_socket)
            connection_options = {
                "unix_socket": str(socket),
                "user": "root",
            }
        else:
            config = check_admin_config(args.admin_client_file)
            connection_options = {
                "read_default_file": str(config),
                "read_default_group": "client",
            }
        import pymysql
        conn = pymysql.connect(
            **connection_options, database=DB_SCHEMA,
            autocommit=True, connect_timeout=8,
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
