"""Fail when credentials or environment files are tracked by Git."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ENV_EXCEPTIONS = {".env.example"}
_SECRET_NAME = rb"(?:password|passwd|token|api[_-]?key|secret)"
_PLACEHOLDER = rb"(?!<?(?:VYPLNIT|PLACEHOLDER|SET[_ -]OUT[_ -]OF[_ -]BAND|\$\{)(?:>)?)"
SENSITIVE_EQUALS_RE = re.compile(
    rb"(?i)\b" + _SECRET_NAME + rb"\b[ \t]*=[ \t]*(?:\\\r?\n[ \t]*|\r?\n[ \t]*)?"
    rb"[\"']?" + _PLACEHOLDER + rb"[^\s\"']{8,}"
)
SENSITIVE_COLON_RE = re.compile(
    rb"(?im)(?:^[ \t]*|[,{][ \t]*)[\"']?" + _SECRET_NAME + rb"[\"']?[ \t]*:[ \t]*"
    rb"[\"']?" + _PLACEHOLDER + rb"[^\s\"']{8,}"
)
_ENV_NAME = rb"[\"'][^\"'\r\n]+[\"']"
_ENV_LOOKUP = re.compile(
    rb"(?i)^(?:os\.environ[ \t]*(?:\[[ \t]*f?" + _ENV_NAME + rb"[ \t]*\]"
    rb"|\.get\([ \t]*" + _ENV_NAME + rb"[ \t]*\))"
    rb"|os\.getenv\([ \t]*" + _ENV_NAME + rb"[ \t]*\))$"
)
_SAFE_ENV_ASSIGNMENT = re.compile(
    rb"(?i)\b(?:password|passwd)\b[\"']?[ \t]*=[ \t]*(?P<value>.+?)(?=[ \t,;#]|$)"
)
CONNECTION_STRING = re.compile(rb"(?i)(?:mysql|mariadb)://[^\s:/]+:[^\s@]+@")


def has_sensitive_value(data: bytes) -> bool:
    """Detect credential-like assignments; allow only direct, no-fallback env reads."""
    sanitized_lines = []
    for line in data.splitlines():
        def remove_safe_env(match: re.Match[bytes]) -> bytes:
            value = match.group("value").strip()
            while True:
                if _ENV_LOOKUP.fullmatch(value):
                    return b""
                if not value.endswith(b")"):
                    return match.group(0)
                value = value[:-1].rstrip()

        sanitized_lines.append(_SAFE_ENV_ASSIGNMENT.sub(remove_safe_env, line))
    candidate = b"\n".join(sanitized_lines)
    return bool(SENSITIVE_EQUALS_RE.search(candidate) or SENSITIVE_COLON_RE.search(candidate))


def scan_tracked_files(root: Path | None = None) -> list[str]:
    root = (root or Path.cwd()).resolve()
    tracked = subprocess.run(
        ["git", "-c", f"safe.directory={root}", "ls-files", "-z"],
        cwd=root, check=True, capture_output=True,
    ).stdout.split(b"\0")
    errors: list[str] = []
    for raw in tracked:
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
            data = (root / name).read_bytes()
        except OSError:
            continue
        if has_sensitive_value(data) or CONNECTION_STRING.search(data):
            errors.append(f"possible credential or connection string: {name}")
    return errors


def main() -> int:
    errors = scan_tracked_files()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Tracked-file secret scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
