"""
runtime_logger.py

Central runtime logging utilities for SAM runs.

- Uses time.perf_counter() for high-resolution, monotonic timing.
- Appends one row per run to a single CSV file: runtimes_master.csv
- Stores:
    - run_id, timestamps, case, paths
    - status (success/fail/timeout/skipped)
    - return_code, runtime_sec, timeout_sec
    - hyperparams_json (serialized dict of hyperparameters)

This module is used by run_launcher.py and (later) optimizer loops.
You normally don't call it directly from the command line.
"""

import csv
import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from time import perf_counter
from pathlib import Path
from typing import Dict, Any, Optional

from .config import CONFIG


# --- Internal dataclass for in-memory context ------------------------------

@dataclass
class _RunContext:
    run_id: str
    case: str
    sam_input_path: str
    output_dir: str
    hyperparams_json: str
    timestamp_start: str
    perf_start: float


# --- Public API ------------------------------------------------------------

def _get_runtime_log_path() -> Path:
    """Return Path object for the central runtime log CSV."""
    return Path(CONFIG["paths"]["runtime_log"]).resolve()


def start_run(case: str,
              hyperparams: Dict[str, Any],
              sam_input_path: str,
              output_dir: str) -> _RunContext:
    """
        Initialize a run context for a SAM run.

        Parameters
        ----------
        case : str
            Logical case/experiment name (e.g. "jsalt1").
        hyperparams : dict
            Hyperparameter dictionary used for this run (node_multiplier, order, etc.).
        sam_input_path : str
            Path to the SAM .i input file.
        output_dir : str
            Directory where outputs/logs for this run are stored (if applicable).

        Returns
        -------
        _RunContext
            An object holding timing + metadata used by end_run().
    """
    run_id = str(uuid.uuid4())
    timestamp_start = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    perf_start = perf_counter()

    return _RunContext(
        run_id=run_id,
        case=case,
        sam_input_path=str(sam_input_path),
        output_dir=str(output_dir),
        hyperparams_json=json.dumps(hyperparams, sort_keys=True),
        timestamp_start=timestamp_start,
        perf_start=perf_start,
    )


def end_run(run_ctx: _RunContext,
            status: str,
            return_code: Optional[int] = None,
            timeout_sec: Optional[float] = None) -> Dict[str, Any]:
    """
    Finalize a run and append a row to the master runtime CSV.

    Parameters
    ----------
    run_ctx : _RunContext
        Context returned by start_run().
    status : str
        One of {"success", "fail", "timeout", "skipped"}.
    return_code : int or None
        Subprocess return code (None for skipped/timeout if not available).
    timeout_sec : float or None
        Timeout used for this run, if any.

    Returns
    -------
    dict
        A dictionary of the logged row (useful for printing or debugging).
    """
    timestamp_end = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    runtime_sec = perf_counter() - run_ctx.perf_start

    # Build row dict
    row = {
        "run_id": run_ctx.run_id,
        "timestamp_start": run_ctx.timestamp_start,
        "timestamp_end": timestamp_end,
        "case": run_ctx.case,
        "sam_input_path": run_ctx.sam_input_path,
        "output_dir": run_ctx.output_dir,
        "status": status,
        "return_code": return_code,
        "runtime_sec": runtime_sec,
        "timeout_sec": timeout_sec,
        "hyperparams_json": run_ctx.hyperparams_json,
    }

    # Append to CSV (create with header if it doesn't exist)
    log_path = _get_runtime_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = log_path.exists()

    fieldnames = list(row.keys())
    with log_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return row
