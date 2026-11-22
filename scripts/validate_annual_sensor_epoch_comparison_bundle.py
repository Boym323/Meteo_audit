#!/usr/bin/env python3
"""Run deterministic validators for 2025/partial-2026 sensor epoch comparison."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('validate_annual_secondary_snapshot_2025.py','validate_annual_secondary_snapshot_2026.py','validate_secondary_sensor_comparison_2025_2026.py'):
 r=subprocess.run([sys.executable,str(root/'scripts'/name)],cwd=root,check=False)
 if r.returncode:raise SystemExit(r.returncode)
print('PASS: 2025/2026 annual sensor snapshot comparison bundle')
