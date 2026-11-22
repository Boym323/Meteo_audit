#!/usr/bin/env python3
"""Run all local validators for the 2026 secondary snapshot bundle."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('validate_annual_secondary_snapshot_2026.py','validate_lightning_field_semantics_2026.py'):
 r=subprocess.run([sys.executable,str(root/'scripts'/name)],cwd=root,check=False)
 if r.returncode: raise SystemExit(r.returncode)
print('PASS: both 2026 secondary snapshot validators')
