#!/usr/bin/env python3
"""#26: backup and verify a full reconstruction restore on a separate empty MariaDB.

Default is read-only dry-run. Execute mode restores ONLY to a proven distinct,
empty instance; it never performs an archive correction or production cutover.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys

SCHEMA = "loucka_reconstruction"
CONFIRMATION = "RESTORE-ONLY-TO-SEPARATE-EMPTY-MARIADB"
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")


class DrillError(RuntimeError):
    pass


def private_file(name):
    path = Path(name)
    if not path.is_absolute() or path.is_symlink():
        raise DrillError("CNF must be absolute and not a symlink")
    s = path.stat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid != os.geteuid():
        raise DrillError("CNF must be a regular file owned by operator")
    if s.st_mode & 0o077 or not s.st_mode & stat.S_IRUSR:
        raise DrillError("CNF file must be private (0600)")
    return path


def client(binary, cnf):
    return [binary, "--defaults-extra-file=" + str(cnf)]


def select(cnf, query, timeout=120):
    try:
        p = subprocess.run(client("mariadb", cnf) + ["-B", "-N", "-e", query],
                           capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise DrillError("MariaDB read-only probe failed") from e
    if p.returncode:
        raise DrillError("MariaDB read-only probe was rejected")
    return [line.split("\t") for line in p.stdout.splitlines() if line.strip()]


def one(rows, columns):
    if len(rows) != 1 or len(rows[0]) != columns:
        raise DrillError("unexpected SQL result cardinality")
    return rows[0]


def instance(cnf):
    return tuple(one(select(cnf, "SELECT @@hostname,@@server_id,@@port,@@datadir"), 4))


def separate_instances(a, b):
    x, y = instance(a), instance(b)
    if (x[0] == y[0] or x[1] == y[1] or x[3] == y[3]
            or x[1] in ("0", "") or y[1] in ("0", "")):
        raise DrillError("NO-GO: host, datadir and server_id must prove separate instances")
    return x, y


def empty_destination(cnf):
    other = select(cnf, "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                   "WHERE SCHEMA_NAME NOT IN "
                   "('mysql','information_schema','performance_schema','sys')")
    if other:
        raise DrillError("NO-GO: destination already contains a user database")


def inventory(cnf):
    tables = select(cnf, "SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA='loucka_reconstruction' "
                    "AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")
    if not tables:
        raise DrillError("empty reconstruction schema")
    for name, engine in tables:
        if not SAFE_NAME.fullmatch(name) or engine != "InnoDB":
            raise DrillError("source tables must be transactional InnoDB with safe names")
    result = [name for name, _ in tables]
    if not {"archive", "reconstruction_changes"}.issubset(result):
        raise DrillError("critical reconstruction tables missing")
    return result


def invariants(cnf):
    row = one(select(cnf,
        "SELECT (SELECT COUNT(*) FROM loucka_reconstruction.archive),"
        "(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes),"
        "(SELECT ROUND(SUM(COALESCE(rain,0))*10,3) FROM loucka_reconstruction.archive "
        "WHERE dateTime>=1625097600 AND dateTime<1627776000),"
        "(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes "
        "WHERE state='applied' AND new_value IS NULL "
        "AND batch_key IN ('qc-extra-temp-outliers-20261123-v1',"
        "'qc-soil-negative-outliers-20261123-v1'))"
        ), 4)
    r = dict(zip(("archive_rows", "change_events", "july_2021_mm",
                  "sensor_null_events"), row))
    if (int(r["archive_rows"]) <= 0 or int(r["change_events"]) <= 0
            or r["july_2021_mm"] != "42.567" or r["sensor_null_events"] != "60"):
        raise DrillError("NO-GO: July 2021 rain or 60 sensor QC events differ")
    return r


def fingerprint(cnf, tables):
    result = {}
    for t in tables:
        if not SAFE_NAME.fullmatch(t):
            raise DrillError("unsafe table name")
        identifier = chr(96) + SCHEMA + chr(96) + "." + chr(96) + t + chr(96)
        count = one(select(cnf, "SELECT COUNT(*) FROM " + identifier, 900), 1)[0]
        checksum = one(select(cnf, "CHECKSUM TABLE " + identifier + " EXTENDED", 3600), 2)[1]
        if checksum in ("NULL", ""):
            raise DrillError("NO-GO: table checksum unsupported")
        result[t] = {"rows": count, "extended_checksum": checksum}
    return result


def dump(source, target):
    options = ["--single-transaction", "--quick", "--skip-lock-tables",
               "--routines", "--events", "--triggers", "--hex-blob",
               "--order-by-primary", "--databases", SCHEMA]
    with target.open("xb") as output:
        os.fchmod(output.fileno(), 0o600)
        p = subprocess.run(client("mariadb-dump", source) + options,
                           stdout=output, stderr=subprocess.DEVNULL,
                           timeout=3600, check=False)
    if p.returncode or target.stat().st_size == 0:
        raise DrillError("source backup failed or is empty")


def restore(target_cnf, dump_path):
    with dump_path.open("rb") as input_file:
        p = subprocess.run(client("mariadb", target_cnf), stdin=input_file,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=3600, check=False)
    if p.returncode:
        raise DrillError("restore failed; discard the separate test instance")


def digest(path):
    sha = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def drill(args):
    source, target = private_file(args.source_cnf), private_file(args.destination_cnf)
    if source == target:
        raise DrillError("two separate CNF files required")
    if not shutil.which("mariadb") or not shutil.which("mariadb-dump"):
        raise DrillError("mariadb and mariadb-dump clients required")
    ids = separate_instances(source, target)
    empty_destination(target)
    tables = inventory(source)
    original = invariants(source)
    if not args.execute:
        return {"status": "DRY_RUN_NO_WRITES", "source": ids[0][:3],
                "destination": ids[1][:3], "invariants": original,
                "table_count": len(tables), "db_writes": 0}

    if args.confirm != CONFIRMATION:
        raise DrillError("explicit confirmation for isolated RESTORE required")
    if not args.receipt_dir or not Path(args.receipt_dir).is_absolute():
        raise DrillError("new absolute receipt directory required")
    out = Path(args.receipt_dir)
    out.mkdir(mode=0o700)  # Existing directory is deliberately forbidden.
    os.chmod(out, 0o700)
    before = fingerprint(source, tables)
    export = out / "loucka_reconstruction.sql"
    dump(source, export)
    if (inventory(source) != tables or invariants(source) != original
            or fingerprint(source, tables) != before):
        raise DrillError("source changed during dump; target NOT modified")
    separate_instances(source, target)
    empty_destination(target)
    restore(target, export)
    if (inventory(target) != tables or invariants(target) != original
            or fingerprint(target, tables) != before):
        raise DrillError("NO-GO: restored schema/invariants/checksums differ")
    receipt = {"status": "PASS_ISOLATED_RESTORE_DRILL_ONLY",
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "source": ids[0][:3], "destination": ids[1][:3],
               "invariants": original, "tables": before,
               "dump_sha256": digest(export), "dump_bytes": export.stat().st_size,
               "source_db_writes": 0, "production_cutover_authorized": False,
               "correction_batch_approved": False}
    with (out / "restore-receipt.json").open("x", encoding="utf-8") as r:
        os.fchmod(r.fileno(), 0o600)
        json.dump(receipt, r, ensure_ascii=False, indent=2, sort_keys=True)
        r.write("\n")
    return {k: v for k, v in receipt.items() if k != "tables"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-cnf", required=True)
    p.add_argument("--destination-cnf", required=True)
    p.add_argument("--receipt-dir")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--confirm", default="")
    args = p.parse_args()
    try:
        print(json.dumps(drill(args), ensure_ascii=False, sort_keys=True))
        return 0
    except (DrillError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print("RESTORE DRILL NO-GO: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
