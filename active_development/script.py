#!/usr/bin/env python
"""
script.py (refactored)

Driver script for running a sweep of SAM cases using the sam_tuner
infrastructure (run_sam_case + centralized runtime logging).

This roughly replaces the old script.py that:
  - edited jsalt*.i templates
  - varied node_multiplier and order
  - ran SAM via subprocess
  - manually tracked runtimes

Now:
  - It calls sam_tuner.run_sam_case() for each configuration.
  - All timing/status info is written to analysis/runtimes_master.csv.
  - You can monitor progress with: python -m sam_tuner.monitor
"""

from pathlib import Path

from sam_tuner.run_launcher import run_sam_case


# ---------- CONTROL PANEL FOR THIS SCRIPT ---------------------------------

# Templates to sweep over (must exist in Templates/)
TEMPLATES = ["jsalt1.i", "jsalt2.i", "jsalt3.i", "jsalt4.i"]

# Node multipliers to test (edit as you like)
NODE_MULT_LIST = [1, 2, 4, 6, 8, 12, 16, 24]

# Orders: 1 = FIRST, 2 = SECOND
ORDERS = [1, 2]

# Optional: extra hyperparameters like HTC can be added per run
BASE_HYPERPARAMS = {
    # "htc": 1000.0,  # example; uncomment and adjust as needed
}


# ---------------------------------------------------------------------------

def main() -> None:
    run_count = 0

    for order in ORDERS:
        for template_name in TEMPLATES:
            # Use template stem as a simple "case name"
            case_name = Path(template_name).stem  # e.g., "jsalt1"

            for nm in NODE_MULT_LIST:
                hyperparams = {
                    **BASE_HYPERPARAMS,
                    "node_multiplier": nm,
                    "order": order,
                }

                print(
                    f"\n=== Running case={case_name} | "
                    f"order={order} | node_multiplier={nm} ==="
                )

                result = run_sam_case(
                    case_name=case_name,
                    template_name=template_name,
                    hyperparams=hyperparams,
                    # timeout_sec=None  # use default from config
                )

                run_count += 1
                print("Run summary:")
                for k, v in result.items():
                    print(f"  {k}: {v}")

    print(f"\nFinished sweep. Total runs: {run_count}")


if __name__ == "__main__":
    main()
