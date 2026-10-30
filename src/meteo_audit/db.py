"""Small MariaDB CLI adapter restricted to one read-only SELECT/SHOW."""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

ALLOWED_DATABASES = frozenset({
    "pocasi-loucka.eu",
    "loucka_reconstruction",
    "pocasi-loucka.eu_GW1000",
    "pocasi-loucka.eu_old",
    "old_weewx",
    "weewx_WH1080",
})
_ALLOWED_START = re.compile(r"\A\s*(SELECT|SHOW)\b", re.IGNORECASE)
_SCHEMA_REFERENCE = re.compile(
    r"\b(?:FROM|JOIN)\s+(`[^`]+`|[A-Za-z0-9_$]+)\s*\.", re.IGNORECASE
)
_FORBIDDEN = re.compile(
    r"\b(INTO|OUTFILE|DUMPFILE|FOR\s+UPDATE|LOCK\s+IN\s+SHARE\s+MODE|"
    r"SLEEP\s*\(|BENCHMARK\s*\(|LOAD_FILE\s*\(|GET_LOCK\s*\(|"
    r"RELEASE_LOCK\s*\(|RELEASE_ALL_LOCKS\s*\(|IS_FREE_LOCK\s*\(|"
    r"IS_USED_LOCK\s*\(|LAST_INSERT_ID\s*\(|NEXTVAL\s*\(|SETVAL\s*\(|"
    r"UUID_SHORT\s*\(|SYS_EXEC\s*\(|SYS_EVAL\s*\()",
    re.IGNORECASE,
)


class ReadOnlyQueryError(ValueError):
    """Raised when a query is outside the deliberately small SQL subset."""


def quote_database(database: str) -> str:
    """Return a quoted schema identifier selected from the fixed allowlist."""
    if database not in ALLOWED_DATABASES:
        raise ReadOnlyQueryError(f"Database is not allowlisted: {database!r}")
    return chr(96) + database + chr(96)


def _load_env(path: Path) -> dict[str, str]:
    if path.exists() and os.name == "posix" and path.stat().st_mode & 0o077:
        raise PermissionError(f"{path} must not be accessible by group or other users")
    values: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    # Environment variables allow a secrets manager to provide credentials
    # without placing them in a file.
    values.update({key: value for key, value in os.environ.items() if key.startswith("DB_")})
    return values


def _validate_select(sql: str) -> None:
    if (
        not isinstance(sql, str)
        or len(sql) > 100_000
        or not _ALLOWED_START.match(sql)
        or ";" in sql
        or "\x00" in sql
        or "--" in sql
        or "/*" in sql
        or "*/" in sql
        or "#" in sql
        or "@" in sql
        or ":=" in sql
        or _FORBIDDEN.search(sql)
    ):
        raise ReadOnlyQueryError("Only one bounded SELECT or SHOW statement without side effects is allowed")
    for match in _SCHEMA_REFERENCE.finditer(sql):
        identifier = match.group(1)
        schema = identifier[1:-1] if identifier.startswith("`") else identifier
        if schema not in ALLOWED_DATABASES:
            raise ReadOnlyQueryError(f"Database is not allowlisted: {schema!r}")


def query(sql: str, *, env_file: str | Path = ".env", timeout: int = 30) -> list[str]:
    """Run a single SELECT or SHOW in a read-only transaction.

    Reuse existing DB_USER / DB_PASSWORD credentials. The SQL validator and
    READ ONLY transaction constrain this client, but do not remove any
    write privileges held by the configured MariaDB account.
    """
    _validate_select(sql)
    if not isinstance(timeout, int) or not 1 <= timeout <= 600:
        raise ValueError("timeout must be an integer between 1 and 600 seconds")
    env = _load_env(Path(env_file))
    required = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD")
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise RuntimeError("Missing database configuration keys: " + ", ".join(missing))
    try:
        port = int(env["DB_PORT"])
    except ValueError as exc:
        raise RuntimeError("DB_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("DB_PORT must be between 1 and 65535")

    fd, config = tempfile.mkstemp(prefix="meteo-audit-", suffix=".cnf")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write("[client]\n")
            for key, option in (("DB_HOST", "host"), ("DB_PORT", "port"),
                                ("DB_USER", "user"),
                                ("DB_PASSWORD", "password")):
                value = env[key].replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                stream.write(f'{option}="{value}"\n')
        try:
            result = subprocess.run(
                ["mariadb", f"--defaults-extra-file={config}", "--batch", "--raw",
                 "--skip-column-names", "--quick", "--connect-timeout=5", "--execute",
                 "SET SESSION TRANSACTION READ ONLY; START TRANSACTION READ ONLY; " + sql + "; ROLLBACK;"],
                check=False, capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"MariaDB read-only query exceeded {timeout} seconds") from exc
        if result.returncode:
            detail = result.stderr.strip().splitlines()
            summary = detail[-1][:500] if detail else "database client returned an error"
            raise RuntimeError(f"MariaDB read-only query failed ({result.returncode}): {summary}")
        return result.stdout.splitlines()
    finally:
        try:
            os.unlink(config)
        except FileNotFoundError:
            pass
