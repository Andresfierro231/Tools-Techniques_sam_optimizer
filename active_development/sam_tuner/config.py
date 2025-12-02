"""
config.py

Central configuration ("control panel") for the SAM optimizer.

You should only need to edit this file for:
- Hyperparameter ranges
- Runtime limits
- Paths (templates, runtime logs, etc.)
"""

from pathlib import Path

# Resolve paths relative to this file, so things work no matter
# where you run Python from (as long as you are inside the repo).
_THIS_DIR = Path(__file__).resolve().parent
# active_development directory (one level up from sam_tuner/)
ACTIVE_DEV_ROOT = _THIS_DIR.parent

CONFIG = {
    # Hyperparameter search space (just a starting point).
    # We will extend this as we formalize IC/BC knobs.
    "hyperparams_space": {
        # Ambient HTC (h_amb) – continuous range interpreted as (min, max)
        "h_amb": (5.0e4, 2.0e5),

        # Node multiplier used in your existing scripts.
        "nodes_mult": [6, 8, 12, 16, 24],

        # Optional: global T_0 range for optimizer candidates.
        # For now we let script.py control T_0 via per-case T0_range,
        # so we don't need to tune T_0 in the optimizer yet.
        # "T_0": (438.0, 462.0),
    },

    # Per-case temperatures & T0 range for script.py
    "temps": {
        # Per-case baseline temperatures pulled from jsalt*.i
        "base_by_case": {
            "jsalt1": {"T_c": 442.15, "T_h": 444.0,  "T_0": 443.0},
            "jsalt2": {"T_c": 446.63, "T_h": 452.0,  "T_0": 450.0},
            "jsalt3": {"T_c": 459.0,  "T_h": 466.0,  "T_0": 460.0},
            "jsalt4": {"T_c": 475.74, "T_h": 480.0,  "T_0": 478.0},
        },
        # Global defaults if a case isn’t in base_by_case
        "defaults": {"T_c": 442.15, "T_h": 444.0, "T_0": 443.0},
        # Instead of discrete offsets, define a range around T0_base:
        #   T_0 ∈ [T0_base - half_width, T0_base + half_width]
        "T0_range": {
            "half_width": 5.0,   # +/- 5 K around the baseline
            "n_points": 5,       # number of points in that range per case
        },
    },

    # Weights for combined objective:
    # score = w_err * normalized_error + w_rt * normalized_runtime
    "objective_weights": {
        "error": 0.7,
        "runtime": 0.3,
    },

    # Runtime limits
    "runtime_limits": {
        # Absolute hard cap in seconds (default: 7 minutes).
        "absolute_sec": 420.0,
        # Optional relative cap (e.g. factor times median runtime).
        "relative_factor": 3.0,
        "enforce_relative": False,  # we'll wire this in later
    },

    # Paths
    "paths": {
        # Where your SAM .i templates live
        "templates_dir": str(ACTIVE_DEV_ROOT / "Templates"),

        # Root where analysis / outputs go
        "results_root": str(ACTIVE_DEV_ROOT / "analysis"),

        # Central runtime log (single source of truth for runtimes)
        "runtime_log": str(ACTIVE_DEV_ROOT / "analysis" / "runtimes_master.csv"),

        # SAM executable (adjust if needed, e.g. "sam-opt-opt" or full path)
        "sam_executable": "sam-opt",

        # Experimental data
        "validation_data": str(ACTIVE_DEV_ROOT.parent / "Validation_Data" / "validation_data.csv"),
    },
}
