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
# active_development directory (one level up from sam_opt/)
ACTIVE_DEV_ROOT = _THIS_DIR.parent

CONFIG = {
    # Hyperparameter search space (just a starting point).
    # We will extend this as we formalize IC/BC knobs.
    "hyperparams_space": {
        # Effective heat transfer coefficient [W/m^2-K] (example range).
        "htc": (100.0, 5000.0),

        # Node multiplier used in your existing scripts.
        "node_multiplier": [1, 2, 4, 8, 16, 24, 32],

        # Finite volume order / quad order (1 = first, 2 = second).
        "order": [1, 2],
    },

    # Weights for a future combined objective:
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
