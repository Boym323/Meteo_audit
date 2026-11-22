#!/usr/bin/env python3
"""Run the active P3 source-first validator and global v3 operation guard."""
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for command in (
    [sys.executable, str(ROOT/'proposals/estimated_short_temperature_gaps_v2/validate.py')],
    [sys.executable, str(ROOT/'scripts/validate_active_proposal_deduplication.py')],
):
    subprocess.run(command, check=True)
print('PASS: active P3 source-first evidence and all-package global safeguards; no DB access.')
