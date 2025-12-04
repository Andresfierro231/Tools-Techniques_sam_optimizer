'''
file_ops.py
File operations to clean up Templates/ folder and have analysis for the optimizer
'''
# file_ops.py (recommended)
from pathlib import Path
import shutil
import glob
import os
def organize_outputs(templates_dir: Path,
                     analysis_root: Path,
                     case_identifier: str):
    """
    Clean Templates/ and move SAM-generated CSV outputs into
    analysis/<case_identifier>/.
    """

    # 1) Remove *_cp* from Templates
    for f in templates_dir.glob("*_cp*"):
        try:
            f.unlink()
            print(f"[cleanup] Removed temp file: {f}")
        except Exception as e:
            print(f"[cleanup] Failed to remove {f}: {e}")

    # 2) Move *nodes_mult* files into analysis/<case_identifier>/
    dest_dir = analysis_root / case_identifier
    dest_dir.mkdir(parents=True, exist_ok=True)

    for f in templates_dir.glob("*nodes_mult*"):
        try:
            shutil.move(str(f), str(dest_dir / f.name))
            print(f"[move] Moved {f.name} → {dest_dir}")
        except Exception as e:
            print(f"[move] Failed to move {f}: {e}")