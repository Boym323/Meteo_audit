#!/usr/bin/env python3
"""Rebuild and validate the reference-data cache inventory."""
import subprocess,sys
for command in ([sys.executable,'scripts/build_reference_data_catalog.py'],[sys.executable,'scripts/validate_reference_data_catalog.py']):
    subprocess.run(command,check=True)
