"""Minimal MariaDB CLI adapter that enforces a read-only transaction per query."""
from __future__ import annotations
import os
import re
import subprocess
import tempfile
from pathlib import Path

_ALLOWED = re.compile(r"\A\s*(SELECT|SHOW)\b", re.IGNORECASE)
_FORBIDDEN = re.compile(r"\b(INTO\s+(OUTFILE|DUMPFILE)|FOR\s+UPDATE|LOCK\s+IN\s+SHARE\s+MODE|SLEEP\s*\(|BENCHMARK\s*\(|LOAD_FILE\s*\()", re.IGNORECASE)

class ReadOnlyQueryError(ValueError):
    pass

def _load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

def query(sql: str, *, env_file: str | Path = '.env', timeout: int = 30) -> list[str]:
    """Execute one SELECT or SHOW and return raw TSV rows; never permits writes."""
    if not _ALLOWED.match(sql) or _FORBIDDEN.search(sql) or ';' in sql or '\x00' in sql:
        raise ReadOnlyQueryError('Only a single SELECT or SHOW statement is allowed')
    env = _load_env(Path(env_file))
    required = ('DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD')
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise RuntimeError('Missing DB configuration keys: ' + ', '.join(missing))
    fd, config = tempfile.mkstemp(prefix='meteo-audit-', suffix='.cnf')
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write('[client]\n')
            for key, option in (('DB_HOST', 'host'), ('DB_PORT', 'port'), ('DB_USER', 'user'), ('DB_PASSWORD', 'password')):
                value = env[key].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                stream.write(f'{option}="{value}"\n')
        result = subprocess.run(
            ['mariadb', f'--defaults-extra-file={config}', '--batch', '--raw', '--skip-column-names', '--quick', '--connect-timeout=5',
             '--execute', 'SET SESSION TRANSACTION READ ONLY; START TRANSACTION READ ONLY; ' + sql + '; ROLLBACK;'],
            check=True, capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.splitlines()
    finally:
        try:
            os.unlink(config)
        except FileNotFoundError:
            pass
