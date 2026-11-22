#!/usr/bin/env python3
"""Offline entry point for repeatable audit validators and run comparison.

This command never opens a database. Database evidence must first be produced
through the approved read-only Weather MCP workflow and saved as bounded files.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/run_audit_checkpoint.py"


def _inside(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def run_validator(args: argparse.Namespace) -> int:
    script = (ROOT / args.script).resolve()
    scripts_dir = (ROOT / "scripts").resolve()
    if not _inside(script, scripts_dir) or not script.is_file() or not script.name.startswith("validate_") or script.suffix != ".py":
        raise ValueError("--script must name an existing scripts/validate_*.py file")
    sources = [(ROOT / p).resolve() for p in args.source]
    outputs = [(ROOT / p).resolve() for p in args.output]
    for path in sources:
        if not path.is_file():
            raise ValueError(f"source does not exist: {path}")
    if any(not _inside(path, ROOT) for path in sources + outputs):
        raise ValueError("source/output paths must stay inside the audit workspace")
    scope = {}
    for item in args.scope:
        if "=" not in item:
            raise ValueError("--scope must use KEY=VALUE")
        key, value = item.split("=", 1)
        if not key or key in scope:
            raise ValueError("scope keys must be nonempty and unique")
        scope[key] = value
    config = {
        "scope": {"analysis": args.name or script.stem, **scope},
        "mode": "offline_validator_only",
        "database_access": "none",
        "started_from_cli_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as stream:
        json.dump(config, stream, ensure_ascii=False, indent=2)
        config_path = Path(stream.name)
    command = [sys.executable, str(WRAPPER), "--config", str(config_path), "--run-root", str((ROOT / args.run_root).resolve()),
               "--source", str(Path(__file__).resolve()), "--source", str(script)]
    for path in sources:
        if path != script:
            command.extend(["--source", str(path)])
    for path in outputs:
        command.extend(["--output", str(path)])
    command.extend(["--", sys.executable, str(script)])
    try:
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    finally:
        config_path.unlink(missing_ok=True)


def compare_manifests(args: argparse.Namespace) -> int:
    left_path = (ROOT / args.left).resolve()
    right_path = (ROOT / args.right).resolve()
    runs_root = (ROOT / args.run_root).resolve()
    if not _inside(left_path, runs_root) or not _inside(right_path, runs_root):
        raise ValueError("manifest paths must be inside the run directory")
    left, right = json.loads(left_path.read_text()), json.loads(right_path.read_text())
    if left.get("status") != "succeeded" or right.get("status") != "succeeded":
        raise ValueError("both runs must have succeeded")
    left_scope, right_scope = left.get("scope"), right.get("scope")
    if left_scope != right_scope:
        raise ValueError("run scopes differ; comparison would be misleading")
    a = {x["path"]: x["sha256"] for x in left.get("outputs", [])}
    b = {x["path"]: x["sha256"] for x in right.get("outputs", [])}
    report = {
        "comparison_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "left_run": left.get("run_id"), "right_run": right.get("run_id"),
        "scope": left_scope,
        "outputs_only_left": sorted(set(a)-set(b)),
        "outputs_only_right": sorted(set(b)-set(a)),
        "unchanged_outputs": sorted(k for k in set(a)&set(b) if a[k] == b[k]),
        "changed_outputs": sorted(k for k in set(a)&set(b) if a[k] != b[k]),
        "comparison_semantics": "SHA-256 equality only; does not establish scientific equivalence",
    }
    out = (ROOT / args.output).resolve()
    if not _inside(out, ROOT):
        raise ValueError("comparison output must stay inside the audit workspace")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run-validator", help="run a local validate_*.py with a SHA-256 manifest")
    run.add_argument("--script", required=True, help="workspace relative scripts/validate_*.py path")
    run.add_argument("--name", help="analysis name in manifest")
    run.add_argument("--scope", action="append", default=[], help="scope metadata KEY=VALUE; repeatable")
    run.add_argument("--source", action="append", default=[], help="workspace relative input file to hash")
    run.add_argument("--output", action="append", default=[], help="workspace relative output/evidence file to hash")
    run.add_argument("--run-root", default="runs")
    run.set_defaults(func=run_validator)
    compare = sub.add_parser("compare", help="compare outputs from two successful same-scope runs")
    compare.add_argument("left", help="workspace relative left manifest path")
    compare.add_argument("right", help="workspace relative right manifest path")
    compare.add_argument("--run-root", default="runs")
    compare.add_argument("--output", required=True, help="workspace relative JSON report path")
    compare.set_defaults(func=compare_manifests)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
