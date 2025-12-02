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

# Node multipliers to test
NODE_MULT_LIST = [1, 2, 4, 6, 8, 12, 16, 24]

# Orders: 1 = FIRST, 2 = SECOND
ORDERS = [1, 2]

# Baseline HTC / IC / BC (global defaults, used if a case is missing)
BASE_HYPERPARAMS = {
    "T_c": 442.15,   # cooler target [K]
    "T_h": 444.0,    # heater BC [K]
    "T_0": 443.0,    # initial loop temp [K]
    "h_amb": 1.0e5,  # ambient HTC [W/m^2-K]
}

# TODO: Per-case baseline temperatures (FILL THESE from each jsalt*.i!) # FIXME 
TEMP_BASE_BY_CASE = {
    "jsalt1": {"T_c": 442.15, "T_h": 444.0, "T_0": 443.0},
    "jsalt2": {"T_c": 442.15, "T_h": 444.0, "T_0": 443.0},  # edit per template
    "jsalt3": {"T_c": 442.15, "T_h": 444.0, "T_0": 443.0},
    "jsalt4": {"T_c": 442.15, "T_h": 444.0, "T_0": 443.0},
}

# Offsets around the baseline T_0 (in Kelvin)
T0_OFFSET_LIST = [-3.0, 0.0, 3.0]

# HTC sweep values
HAMB_LIST = [5.0e4, 1.0e5, 2.0e5]



# ---------------------------------------------------------------------------

def main() -> None:
    run_count = 0

    for order in ORDERS:
        for template_name in TEMPLATES:
            case_name = Path(template_name).stem  # e.g., "jsalt1"

            # Get per-case baselines; fall back to global BASE_HYPERPARAMS if missing
            temps_base = TEMP_BASE_BY_CASE.get(case_name, BASE_HYPERPARAMS)
            T_c_base = temps_base.get("T_c", BASE_HYPERPARAMS["T_c"])
            T_h_base = temps_base.get("T_h", BASE_HYPERPARAMS["T_h"])
            T0_base = temps_base.get("T_0", BASE_HYPERPARAMS["T_0"])

            for T0_offset in T0_OFFSET_LIST:
                T0_value = T0_base + T0_offset

                for hamb in HAMB_LIST:
                    for nm in NODE_MULT_LIST:
                        # Start from BASE_HYPERPARAMS and override temps per case
                        hyperparams = {
                            **BASE_HYPERPARAMS,
                            "T_c": T_c_base,
                            "T_h": T_h_base,
                            "T_0": T0_value,        # baseline + offset
                            "T0_offset": T0_offset, # optional: logged in JSON
                            "h_amb": hamb,
                            "node_multiplier": nm,
                            "order": order,
                        }

                        print(
                            f"\n=== Running case={case_name} | "
                            f"order={order} | node_multiplier={nm} | "
                            f"h_amb={hamb} | "
                            f"T_c={T_c_base} | T_h={T_h_base} | "
                            f"T_0={T0_value} (offset {T0_offset}) ==="
                        )

                        result = run_sam_case(
                            case_name=case_name,
                            template_name=template_name,
                            hyperparams=hyperparams,
                            # timeout_sec=None  # or use CONFIG runtime limit
                        )

                        run_count += 1
                        print("Run summary:")
                        for k, v in result.items():
                            print(f"  {k}: {v}")

    print(f"\nFinished sweep. Total runs: {run_count}")

if __name__ == "__main__":
    main()
