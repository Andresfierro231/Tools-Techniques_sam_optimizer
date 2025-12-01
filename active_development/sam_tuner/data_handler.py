"""
data_handler.py

Utilities to build an ML-ready dataset for the SAM optimizer.

This module is responsible for:
  - Loading the validation analysis CSV produced by csv_analysis.py
    (typically 'validation_analysis_full.csv').
  - Loading the centralized runtime log 'runtimes_master.csv'.
  - Building a combined DataFrame with:
      * features (hyperparameters, metadata)
      * targets (error metrics, runtime)

For now, we keep this simple and opinionated:

  - We assume there is a CSV called 'validation_analysis_full.csv'
    under CONFIG["paths"]["results_root"] (e.g. active_development/analysis).

  - We expect this file to contain at least:
      * 'rmse_K'              (main error metric)
      * 'script_runtime'      (runtime in seconds, from csv_maker/csv_analysis)
      * 'nodes_mult'          (node multiplier)
      * 'order'               (FE/FV order)
    plus other columns (prefix, case, per-TP errors, etc.).

  - We do NOT yet rely on runtimes_master.csv for runtime, because your
    current csv_maker/csv_analysis pipeline already propagates
    script_runtime from earlier runs. We can merge runtimes_master later.

You can adapt FEATURE_COLUMNS and TARGET_COLUMNS below once you inspect
your actual 'validation_analysis_full.csv' content.
"""

from pathlib import Path
from typing import Tuple, Optional, List

import pandas as pd

from .config import CONFIG


# === CONFIG-LIKE CONSTANTS (tweak here as you learn the CSV schema) ========

# Default file name for the full validation analysis CSV.
VALIDATION_ANALYSIS_FILENAME = "validation_analysis_full.csv"

# Names of the default target columns in the validation analysis CSV.
ERROR_COLUMN = "rmse_K"          # main accuracy metric
RUNTIME_COLUMN = "script_runtime"  # runtime in seconds (as used in csv_analysis)

# Minimal feature set we know should exist (based on csv_analysis.py):
#   - nodes_mult: discretization parameter (node multiplier)
#   - order:      discretization order (1 or 2)
# You can add more (e.g., 'case', 'prefix', 'htc', etc.) as needed.
FEATURE_COLUMNS: List[str] = [
    "nodes_mult",
    "order",
]


# === PATH HELPERS ==========================================================

def _results_root() -> Path:
    """Return the root path where analysis CSVs live."""
    return Path(CONFIG["paths"]["results_root"]).resolve()


def _validation_analysis_path() -> Path:
    """Compute the expected path to 'validation_analysis_full.csv'."""
    return _results_root() / VALIDATION_ANALYSIS_FILENAME


def _runtime_log_path() -> Path:
    """Path to the central runtime log."""
    return Path(CONFIG["paths"]["runtime_log"]).resolve()


# === LOADERS ===============================================================

def load_validation_analysis() -> pd.DataFrame:
    """
    Load the validation analysis CSV (full table of runs + error metrics).

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per SAM run, including columns like:
        'nodes_mult', 'order', 'rmse_K', 'script_runtime', etc.

    Raises
    ------
    FileNotFoundError
        If the expected CSV is not found.
    """
    path = _validation_analysis_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Validation analysis CSV not found: {path}\n"
            "Make sure you have run csv_analysis.py to generate "
            "'validation_analysis_full.csv'."
        )
    df = pd.read_csv(path)
    return df


def load_runtime_log() -> Optional[pd.DataFrame]:
    """
    Load the centralized runtime log (runtimes_master.csv) if it exists.

    Returns
    -------
    pd.DataFrame or None
        The runtime log, or None if the file does not exist yet.
    """
    path = _runtime_log_path()
    if not path.exists():
        return None
    return pd.read_csv(path)


# === DATASET BUILDER =======================================================

def build_basic_dataset(
    error_col: str = ERROR_COLUMN,
    runtime_col: str = RUNTIME_COLUMN,
    feature_cols: Optional[list] = None,
    drop_na_targets: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Build a basic (X, y_error, y_runtime) dataset from validation_analysis_full.csv.

    Parameters
    ----------
    error_col : str
        Column name to use as the main error target (default: 'rmse_K').
    runtime_col : str
        Column name to use as the runtime target (default: 'script_runtime').
        NOTE: For now, this comes from the validation analysis CSV, not the
        centralized runtimes_master.csv, to stay compatible with your existing
        pipeline. We can merge in runtimes_master later.
    feature_cols : list or None
        List of column names to use as features. If None, uses FEATURE_COLUMNS
        defined at the top of this module.
    drop_na_targets : bool
        If True, drop rows where either error_col or runtime_col is NaN.

    Returns
    -------
    (X, y_error, y_runtime) : (pd.DataFrame, pd.Series, pd.Series)
        - X: feature matrix
        - y_error: error target (e.g. rmse_K)
        - y_runtime: runtime target (e.g. script_runtime)
    """
    df = load_validation_analysis()

    if feature_cols is None:
        feature_cols = FEATURE_COLUMNS

    # Check that necessary columns exist
    missing_features = [c for c in feature_cols if c not in df.columns]
    missing_targets = [c for c in [error_col, runtime_col] if c not in df.columns]

    if missing_features:
        raise KeyError(
            f"Missing feature columns in validation_analysis_full.csv: {missing_features}\n"
            f"Available columns are:\n{list(df.columns)}"
        )
    if missing_targets:
        raise KeyError(
            f"Missing target columns in validation_analysis_full.csv: {missing_targets}\n"
            f"Available columns are:\n{list(df.columns)}"
        )

    # Optionally drop rows with invalid targets
    if drop_na_targets:
        df = df.dropna(subset=[error_col, runtime_col])

    X = df[feature_cols].copy()
    y_error = df[error_col].copy()
    y_runtime = df[runtime_col].copy()

    return X, y_error, y_runtime
