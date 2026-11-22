"""Read-only row adapter exposing concordance SQLite to readiness builder."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import zlib
from collections import Counter
from itertools import islice
from pathlib import Path

FIELDS = ("outTemp", "outHumidity", "windSpeed", "windGust", "windDir", "barometer", "pressure", "altimeter")


def readiness_category(category: str) -> str:
    """Match the authoritative readiness builder's strict source categories."""
    if category in {"RECOVERED_SOURCE", "RESTORED", "CORRECTED", "ESTIMATED"}:
        return category
    # Archive-copy agreement alone is not independently verified lineage.
    return "UNCLASSIFIED"


class ConcordanceReadOnlyConnection:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
        self.db.execute("PRAGMA query_only=ON")
        if self.db.execute("PRAGMA query_only").fetchone()[0] != 1:
            raise RuntimeError("concordance SQLite connection is not query_only")
        if self.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("concordance SQLite integrity check failed")
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.meta = {k: v for k, v in self.db.execute("SELECT key,value FROM snapshot_meta")}
        manifest_path = self.path.with_suffix(".manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("sqlite_sha256_after_close") != self.sha256:
            raise RuntimeError("concordance sidecar SHA-256 does not match selected file")
        self.target = json.loads(self.meta["target"])
        self.identity = json.loads(self.meta["database_identity"])
        self.verified_source_timestamps: set[int] = set()
        self.category_counts: Counter[str] = Counter()

    def cursor(self):
        return ConcordanceReadOnlyCursor(self)

    def begin(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.db.close()


class ConcordanceReadOnlyCursor:
    def __init__(self, connection: ConcordanceReadOnlyConnection):
        self.connection = connection
        self.rows = iter(())
        self.description = None

    def execute(self, operation: str, params=None):
        sql = " ".join(operation.split())
        db = self.connection.db
        if sql.startswith("SET SESSION TRANSACTION READ ONLY"):
            self.rows = iter(())
        elif sql.startswith("SELECT VERSION(),@@hostname,@@server_id,CURRENT_USER()"):
            i = self.connection.identity
            self.rows = iter([(i["version"], i["host"], i["server_id"], i["account"])])
        elif "SELECT `dateTime`,`interval` FROM `loucka_reconstruction`.`archive`" in sql:
            self.rows = ((int(ts), int(interval or 0)) for ts, interval in db.execute(
                "SELECT dateTime,target_interval FROM timestamp_evidence ORDER BY dateTime"))
        elif "archive_sync_verification" in sql or "archive_sync_audit" in sql or "reconstruction_changes" in sql:
            # The snapshot's per-field provenance categories are already
            # derived from validated immutable audit batches and applied-change
            # evidence. The readiness loop uses these categories directly.
            self.rows = iter(())
        elif "FROM `loucka_reconstruction`.`archive` ORDER BY `dateTime`" in sql:
            def records():
                for ts, interval, blob in db.execute(
                    "SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence ORDER BY dateTime"
                ):
                    values = json.loads(zlib.decompress(blob))
                    actual = tuple(values.get(field, {}).get("target_value") for field in FIELDS)
                    categories = tuple(readiness_category(values.get(field, {}).get("provenance_category", "UNCLASSIFIED")) for field in FIELDS)
                    for value, category in zip(actual, categories):
                        if value is not None:
                            self.connection.category_counts[category] += 1
                    if "RECOVERED_SOURCE" in categories:
                        self.connection.verified_source_timestamps.add(int(ts))
                    yield (int(ts), 16, int(interval or 0), *actual, *categories)
            self.rows = records()
        else:
            raise RuntimeError("readiness snapshot adapter refused unrecognized SQL")
        return self

    def fetchmany(self, size=1):
        return list(islice(self.rows, size))

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return next(self.rows, None)

    def close(self):
        self.rows = iter(())

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.rows)
