#!/usr/bin/env python3
"""Validate annual lightning aggregate and cross-archive evidence together."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('validate_lightning_field_semantics_2026.py','validate_lightning_cross_archive_2026.py'):
 r=subprocess.run([sys.executable,str(root/'scripts'/name)],cwd=root,check=False)
 if r.returncode:raise SystemExit(r.returncode)
print('PASS: annual and cross-archive lightning evidence')
