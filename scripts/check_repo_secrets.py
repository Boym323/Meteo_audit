"""Fail when credentials or environment files are tracked by Git."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TRACKED = subprocess.run(
    ["git", "-c", f"safe.directory={Path.cwd().resolve()}", "ls-files", "-z"],
    check=True, capture_output=True,
).stdout.split(b"\0")
ENV_EXCEPTIONS = {".env.example"}
SENSITIVE_RE = re.compile(
    rb"(?i)(?:password|passwd|token|api[_-]?key|secret)\s*[:=]\s*"
    rb"[\"']?(?!<?(?:VYPLNIT|PLACEHOLDER|SET[_ -]OUT[_ -]OF[_ -]BAND|\$\{)(?:>)?)[^\s\"']{8,}"
)
CONNECTION_STRING = re.compile(rb"(?i)(?:mysql|mariadb)://[^\s:/]+:[^\s@]+@")
errors: list[str] = []
for raw in TRACKED:
    if not raw:
        continue
    name = raw.decode("utf-8", errors="replace")
    base = Path(name).name
    if base.startswith(".env") and base not in ENV_EXCEPTIONS:
        errors.append(f"tracked environment file: {name}")
        continue
    if base == ".env.example":
        continue
    try:
        data = Path(name).read_bytes()
    except OSError:
        continue
    if SENSITIVE_RE.search(data) or CONNECTION_STRING.search(data):
        errors.append(f"possible credential or connection string: {name}")

if errors:
    for error in errors:
        print(error, file=sys.stderr)
    raise SystemExit(1)
print("Tracked-file secret scan passed.")
