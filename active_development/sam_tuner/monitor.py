"""
monitor.py

Simple live monitor for SAM optimizer runs.

Usage (from active_development/ or anywhere in the repo):

    python -m sam_opt.monitor

or

    cd active_development
    python sam_opt/monitor.py

This will:
- Re-read the central runtime log every few seconds
- Print:
    - Total runs
    - Counts by status (success/fail/timeout/skipped)
    - Basic runtime stats (min/median/max) for completed runs
"""

import os
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import CONFIG


def _clear_screen():
    """Clear the terminal screen in a cross-platform way."""
    os.system("cls" if os.name == "nt" else "clear")


def _load_runtime_df() -> Optional[pd.DataFrame]:
    """Load the runtime log into a DataFrame if it exists, else None."""
    log_path = Path(CONFIG["paths"]["runtime_log"]).resolve()
    if not log_path.exists():
        return None
    return pd.read_csv(log_path)


def _print_summary(df: pd.DataFrame):
    """Print a simple textual summary of the current runs."""
    total = len(df)
    by_status = df["status"].value_counts().to_dict()

    # Completed = everything except skipped.
    completed_mask = df["status"].isin(["success", "fail", "timeout"])
    completed = df[completed_mask]
    n_completed = len(completed)

    print("=== SAM Optimizer Live Monitor ===")
    print(f"Runtime log: {CONFIG['paths']['runtime_log']}")
    print()
    print(f"Total runs logged: {total}")
    print("By status:")
    for status in ["success", "fail", "timeout", "skipped"]:
        print(f"  {status:8s}: {by_status.get(status, 0)}")
    print()

    if n_completed > 0:
        runtimes = completed["runtime_sec"]
        print("Completed run runtimes [s]:")
        print(f"  min   : {runtimes.min():.2f}")
        print(f"  median: {runtimes.median():.2f}")
        print(f"  max   : {runtimes.max():.2f}")
    else:
        print("No completed runs yet.")

    print()
    print("Press Ctrl+C to exit.")


def main(poll_interval: float = 5.0):
    """
    Periodically load the runtime log and print a summary.

    Parameters
    ----------
    poll_interval : float
        Number of seconds between refreshes.
    """
    try:
        while True:
            _clear_screen()
            df = _load_runtime_df()
            if df is None:
                print("No runtime log found yet.")
                print(f"Expected at: {CONFIG['paths']['runtime_log']}")
            else:
                _print_summary(df)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nMonitor terminated by user.")


if __name__ == "__main__":
    main()
