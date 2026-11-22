#!/usr/bin/env python3
"""Run validators for annual sensor aggregates and three-year comparison."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('validate_annual_secondary_snapshot_2024.py','validate_annual_secondary_snapshot_2025.py','validate_annual_secondary_snapshot_2026.py','validate_secondary_sensor_comparison_2024_2026.py'):
 r=subprocess.run([sys.executable,str(root/'scripts'/name)],cwd=root,check=False)
 if r.returncode:raise SystemExit(r.returncode)
print('PASS: 2024-2026 annual secondary sensor coverage bundle')
