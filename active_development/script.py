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
from sam_tuner.config import CONFIG
import numpy as np 


# ---------- CONTROL PANEL FOR THIS SCRIPT ---------------------------------

# Templates to sweep over (must exist in Templates/)
TEMPLATES = ["jsalt1.i", "jsalt2.i", "jsalt3.i", "jsalt4.i"]

NODE_MULT_LIST =    [6, 8, 12, 16, 24]          # Node multipliers to test
ORDERS =            [1, 2]                      # Orders: 1 = FIRST, 2 = SECOND

# Baseline HTC / IC / BC (global defaults, used if a case is missing)
BASE_HYPERPARAMS = {
    "T_c": 442.15,   # cooler target [K]
    "T_h": 444.0,    # heater BC [K]
    "T_0": 443.0,    # initial loop temp [K]
    "h_amb": 1.0e5,  # ambient HTC [W/m^2-K]
}

# Per-case baseline temperatures pulled from jsalt*.i templates
TEMP_BASE_BY_CASE = CONFIG["temps"]["base_by_case"]
TEMP_DEFAULTS = CONFIG["temps"]["defaults"]
T0_RANGE = CONFIG["temps"]["T0_range"]

# HTC sweep values
HAMB_LIST = [5.0e4, 1.0e5, 2.0e5]



# ---------------------------------------------------------------------------

def main() -> None:
    run_count = 0

    for order in ORDERS:
        for template_name in TEMPLATES:
            case_name = Path(template_name).stem  # e.g. "jsalt1"

            temps_base = TEMP_BASE_BY_CASE.get(case_name, TEMP_DEFAULTS)
            T_c_base = temps_base["T_c"]
            T_h_base = temps_base["T_h"]
            T0_base  = temps_base["T_0"]

            half_width = float(T0_RANGE["half_width"])
            n_points   = int(T0_RANGE["n_points"])

            T0_min = T0_base - half_width
            T0_max = T0_base + half_width

            # Option A: small grid in the range
            T0_values = np.linspace(T0_min, T0_max, n_points)

            # Option B (comment A out, uncomment B) for random sampling:
            # T0_values = np.random.uniform(T0_min, T0_max, size=n_points)

            for T0_value in T0_values:
                for hamb in HAMB_LIST:
                    for nm in NODE_MULT_LIST:
                        hyperparams = {
                            "T_c": T_c_base,
                            "T_h": T_h_base,
                            "T_0": float(T0_value),
                            "h_amb": hamb,
                            "node_multiplier": nm,
                            "order": order,
                        }

                        print(
                            f"\n=== Running case={case_name} | "
                            f"order={order} | node_multiplier={nm} | "
                            f"h_amb={hamb} | "
                            f"T_c={T_c_base} | T_h={T_h_base} | "
                            f"T_0={T0_value:.2f} "
                            f"(range [{T0_min:.2f}, {T0_max:.2f}]) ==="
                        )

                        result = run_sam_case(
                            case_name=case_name,
                            template_name=template_name,
                            hyperparams=hyperparams,
                        )

                        run_count += 1
                        print("Run summary:")
                        for k, v in result.items():
                            print(f"  {k}: {v}")

    print(f"\nFinished sweep. Total runs: {run_count}")

if __name__ == "__main__":
    main()
