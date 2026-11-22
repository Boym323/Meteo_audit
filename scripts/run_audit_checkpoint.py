#!/usr/bin/env python3
"""Run a local audit command and record a hash-based, resumable checkpoint.

The wrapper never connects to a database itself. Callers provide a command,
non-secret JSON configuration, source files and expected output files. The
child process output is captured to a per-run log.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path: Path, root: Path) -> dict[str, object]:
    resolved = path.resolve()
    try:
        label = str(resolved.relative_to(root.resolve()))
    except ValueError:
        label = str(resolved)
    return {"path": label, "bytes": resolved.stat().st_size, "sha256": sha256(resolved)}


def safe_command(command: list[str]) -> list[str]:
    """Redact common secret-bearing CLI options before logging the argv."""
    safe: list[str] = []
    redact_next = False
    for argument in command:
        if redact_next:
            safe.append("<redacted>")
            redact_next = False
            continue
        if re.search(r"(?i)(password|passwd|token|secret|api[-_]?key)(=|$)", argument):
            if "=" in argument:
                safe.append(argument.split("=", 1)[0] + "=<redacted>")
            else:
                safe.append(argument)
                redact_next = True
            continue
        # Avoid leaking credentials embedded in a connection URL.
        safe.append(re.sub(r"(?i)(://[^:/@]+):[^@/]+@", r"\1:<redacted>@", argument))
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True,
                        help="Non-secret JSON file describing scope and parameters")
    parser.add_argument("--source", type=Path, action="append", default=[],
                        help="Input file to hash; repeat for each source artifact")
    parser.add_argument("--output", type=Path, action="append", default=[],
                        help="Expected output file to hash after the command; repeatable")
    parser.add_argument("--run-root", type=Path, default=Path("runs"))
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="Command to run after --, for example -- python3 script.py")
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a command after --")
    config_path = args.config.resolve()
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read valid JSON config: {exc}")
    if not isinstance(config, dict):
        parser.error("config JSON must be an object")
    for path in args.source:
        if not path.is_file():
            parser.error(f"source path must be an existing file: {path}")
    for path in args.output:
        if path.exists() and not path.is_file():
            parser.error(f"output path must be a file path: {path}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = args.run_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    root = Path.cwd()
    log_path = run_dir / "run.log"
    started = datetime.now(timezone.utc)
    recorded_command = safe_command(command)
    with log_path.open("w", encoding="utf-8") as log:
        log.write("$ " + shlex.join(recorded_command) + "\n")
        log.flush()
        try:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    check=False, shell=False)
            exit_code = result.returncode
        except OSError as exc:
            log.write(f"\nEXECUTION_ERROR: {type(exc).__name__}: {exc}\n")
            exit_code = 127
    ended = datetime.now(timezone.utc)
    manifest = {
        "run_id": run_id,
        "started_utc": started.isoformat(timespec="seconds"),
        "ended_utc": ended.isoformat(timespec="seconds"),
        "status": "succeeded" if exit_code == 0 else "failed",
        "exit_code": exit_code,
        "scope": config.get("scope"),
        "configuration": config,
        "command": recorded_command,
        "database_access": "wrapper has no DB client; child command safety must be reviewed",
        "analysis_code": file_record(Path(__file__), root),
        "configuration_file": file_record(config_path, root),
        "sources": [file_record(path, root) for path in args.source],
        "outputs": [file_record(path, root) for path in args.output if path.is_file()],
        "missing_outputs": [str(path) for path in args.output if not path.is_file()],
        "log": file_record(log_path, root),
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"run_id={run_id} status={manifest['status']} manifest={manifest_path}")
    if manifest["missing_outputs"] and exit_code == 0:
        print("ERROR: expected output file(s) missing", file=sys.stderr)
        return 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
