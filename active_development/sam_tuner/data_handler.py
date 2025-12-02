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
      * 'nodes_mult'          (node multiplier)
      * 'order'               (FE/FV order or some order label)
    plus other columns (prefix, case, per-TP errors, etc.).

  - Runtime:
      * If 'script_runtime' is present and non-NaN, we can use it.
      * Otherwise, we try to merge runtime_sec from runtimes_master.csv
        using the input filename as a key, and expose it as
        'runtime_merged_sec'.

You can adapt FEATURE_COLUMNS and TARGET_COLUMNS below once you inspect
your actual 'validation_analysis_full.csv' content.
"""

from pathlib import Path
from typing import Tuple, Optional, List
import json  
import pandas as pd

from .config import CONFIG


# === CONFIG-LIKE CONSTANTS (tweak here as you learn the CSV schema) ========

# Default file name for the full validation analysis CSV.
VALIDATION_ANALYSIS_FILENAME = "validation_analysis_full.csv"

# Names of the default target columns in the validation analysis CSV.
ERROR_COLUMN = "rmse_K"  # main accuracy metric

# For runtime, we now prefer 'runtime_merged_sec' (from runtimes_master.csv).
RUNTIME_COLUMN_DEFAULT = "runtime_merged_sec"

# Minimal feature set we know should exist (based on csv_analysis.py):
#   - nodes_mult: discretization parameter (node multiplier) from csv_analysis (parsed from filenames)
#   - order:      discretization order (1 or 2 or label)
#   - h_amb     : from hyperparams_json in runtimes_master.csv
# You can add more (e.g., 'case', 'prefix', etc.) as needed.
FEATURE_COLUMNS: List[str] = [
    "nodes_mult",
    # "order",  # we'll add 'order' later when the analysis CSV actually has 1/2 here
]

# Default file name for the full validation analysis CSV.
VALIDATION_ANALYSIS_FILENAME = "validation_analysis_full.csv"

# Names of the default target columns in the validation analysis CSV.
ERROR_COLUMN = "rmse_K"                 # main accuracy metric
RUNTIME_COLUMN_DEFAULT = "runtime_merged_sec"  # runtime from merged log

# Minimal feature set:


# === PATH HELPERS ==========================================================

def _results_root() -> Path:
    """Return the root path where analysis CSVs live."""
    return Path(CONFIG["paths"]["results_root"]).resolve()


def _validation_analysis_path() -> Path:
    """
    Compute the expected path to 'validation_analysis_full.csv'.

    We try a couple of locations:
      1) <results_root>/validation_analysis_full.csv
      2) <results_root>/analysis/validation_analysis_full.csv

    This covers both:
      - CONFIG["paths"]["results_root"] = "active_development/analysis"
      - csv_analysis.py writing into "analysis/analysis/..."
    """
    root = _results_root()
    direct = root / VALIDATION_ANALYSIS_FILENAME
    nested = root / "analysis" / VALIDATION_ANALYSIS_FILENAME

    if direct.exists():
        return direct
    if nested.exists():
        return nested

    # If not found, raise a detailed error
    raise FileNotFoundError(
        "Validation analysis CSV not found in expected locations:\n"
        f"  1) {direct}\n"
        f"  2) {nested}\n"
        "Make sure you have run csv_analysis.py and that CONFIG['paths']['results_root'] "
        "matches where those files are written."
    )


def _runtime_log_path() -> Path:
    """Path to the central runtime log."""
    return Path(CONFIG["paths"]["runtime_log"]).resolve()


# === LOADERS ===============================================================

def load_validation_analysis() -> pd.DataFrame:
    """
    Load the validation analysis CSV (full table of runs + error metrics).
    """
    path = _validation_analysis_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Validation analysis CSV not found: {path}\n"
            "Make sure you have run csv_analysis.py to generate "
            "'validation_analysis_full.csv'."
        )
    df = pd.read_csv(path)
    print(f"[data_handler] Loaded validation analysis from: {path}")
    print(f"[data_handler] Shape: {df.shape}")
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
        print(f"[data_handler] No runtime log found at: {path}")
        return None
    df = pd.read_csv(path)
    print(f"[data_handler] Loaded runtime log from: {path}")
    print(f"[data_handler] Runtime log shape: {df.shape}")
    return df


# === RUNTIME MERGE HELPERS =================================================

def _derive_input_basename_from_source_file(source_file: str) -> str:
    """
    Map a validation 'source_file' to an input basename used in runtimes_master.

    Given a 'source_file' from validation_analysis (e.g.
    'jsalt1_nodes_mult_by_6_ord2_csv.csv'), derive the corresponding .i input basename:
    'jsalt1_nodes_mult_by_6_ord2.i'

    Example:
      source_file = 'jsalt1_nodes_mult_by_6_ord2_csv.csv'
      -> 'jsalt1_nodes_mult_by_6_ord2.i'

    This matches the basename of sam_input_path in runtimes_master.csv.
    """
    s = str(source_file)
    # Strip trailing '_csv.csv' or '.csv' if present
    if s.endswith("_csv.csv"):
        base = s[:-len("_csv.csv")]
    elif s.endswith(".csv"):
        base = s[:-len(".csv")]
    else:
        base = s
    return base + ".i"
def _merge_runtime_from_log(df_val: pd.DataFrame) -> pd.DataFrame:
    """
    Merge runtime information from runtimes_master.csv into the validation DataFrame.

    We:
      - compute 'input_basename' from 'source_file' in df_val
      - compute 'input_basename' from sam_input_path in runtimes_master
      - group runtimes by input_basename:
          * median runtime_sec -> runtime_merged_sec
          * first hp_* values (e.g. hp_h_amb, hp_T_c, etc.)
      - left-merge onto df_val

    Returns
    -------
    pd.DataFrame
        The validation DataFrame with:
          - 'runtime_merged_sec'
          - 'h_amb' (if present in hyperparams_json)
          - possibly other IC/BC columns (T_c, T_h, T_0, ...)
    """
    df = df_val.copy()

    if "source_file" not in df.columns:
        print("[data_handler] WARNING: 'source_file' column missing in validation data; "
              "cannot merge runtime. Creating runtime_merged_sec as NaN.")
        df["runtime_merged_sec"] = pd.NA
        return df

    runtime_df = _load_runtime_log_with_hyperparams()
    if runtime_df is None:
        df["runtime_merged_sec"] = pd.NA
        return df

    # Derive input_basename in runtime log
    runtime_df = runtime_df.copy()
    runtime_df["input_basename"] = runtime_df["sam_input_path"].astype(str).map(
        lambda p: Path(p).name
    )

    # Build aggregation dict
    agg_dict = {"runtime_sec": "median"}
    # For hyperparameter columns, take the first value (we assume each .i has consistent hyperparams)
    for col in runtime_df.columns:
        if col.startswith("hp_"):
            agg_dict[col] = "first"

    grouped = runtime_df.groupby("input_basename", as_index=False).agg(agg_dict)
    grouped = grouped.rename(columns={"runtime_sec": "runtime_merged_sec"})

    # Map validation source_file -> input_basename
    df["input_basename"] = df["source_file"].astype(str).map(
        _derive_input_basename_from_source_file
    )

    # Merge in runtime + hp_* columns
    df = df.merge(grouped, on="input_basename", how="left")

    # Convenience: if hp_h_amb exists, expose it as 'h_amb'
    if "hp_h_amb" in df.columns and "h_amb" not in df.columns:
        df["h_amb"] = df["hp_h_amb"]

    # (Optional) same idea for T_c, T_h, T_0 if you want:
    for hp_name, out_name in [
        ("hp_T_c", "T_c"),
        ("hp_T_h", "T_h"),
        ("hp_T_0", "T_0"),
        ("hp_node_multiplier", "node_multiplier_hp"),
    ]:
        if hp_name in df.columns and out_name not in df.columns:
            df[out_name] = df[hp_name]

    return df

def _merge_runtime_from_log(df_val: pd.DataFrame) -> pd.DataFrame:
    """
    Merge runtime information from runtimes_master.csv into the validation DataFrame.

    We:
      - compute 'input_basename' from 'source_file' in df_val
      - compute 'input_basename' from sam_input_path in runtimes_master
      - group runtimes by input_basename (taking median runtime_sec over successes)
      - left-merge onto df_val as 'runtime_merged_sec'

    Returns
    -------
    pd.DataFrame
        The validation DataFrame with an extra 'runtime_merged_sec' column (may have NaNs).
    """
    rt = load_runtime_log()
    if rt is None:
        print("[data_handler] No runtime log available; skipping runtime merge.")
        df_val["runtime_merged_sec"] = pd.NA
        return df_val

    # Derive basename from sam_input_path
    rt = rt.copy()
    rt["input_basename"] = rt["sam_input_path"].astype(str).map(
        lambda p: Path(p).name
    )

    # Prefer successful runs; if none, fall back to all
    if "status" in rt.columns:
        rt_success = rt[rt["status"] == "success"]
        if rt_success.empty:
            rt_success = rt
    else:
        rt_success = rt

    # Aggregate: median runtime_sec per input_basename
    grouped = (
        rt_success.groupby("input_basename", as_index=False)["runtime_sec"]
        .median()
        .rename(columns={"runtime_sec": "runtime_merged_sec"})
    )

    print("[data_handler] Runtime aggregation by input_basename:")
    print(grouped.head())

    df = df_val.copy()
    if "source_file" not in df.columns:
        print("[data_handler] WARNING: 'source_file' column missing in validation data; "
              "cannot merge runtime. Creating runtime_merged_sec as NaN.")
        df["runtime_merged_sec"] = pd.NA
        return df

    df["input_basename"] = df["source_file"].astype(str).map(
        _derive_input_basename_from_source_file
    )

    df = df.merge(grouped, on="input_basename", how="left")
    return df


# === DATASET BUILDER =======================================================
def build_basic_dataset(
    error_col: str = ERROR_COLUMN,
    runtime_col: str = RUNTIME_COLUMN_DEFAULT,
    feature_cols: Optional[list] = None,
    drop_na_targets: bool = True,
    merge_runtime: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Build a basic (X, y_error, y_runtime) dataset from validation_analysis_full.csv
    and runtimes_master.csv.

    Parameters
    ----------
    error_col : str
        Column name to use as the main error target (default: 'rmse_K').
    runtime_col : str
        Column name to use as the runtime target (default: 'runtime_merged_sec').
    feature_cols : list or None
        List of column names to use as features. If None, uses FEATURE_COLUMNS.
    drop_na_targets : bool
        If True, drop rows where either error_col or runtime_col is NaN.
    merge_runtime : bool
        If True, call _merge_runtime_from_log to bring in runtime_merged_sec
        and h_amb from runtimes_master.csv.

    Returns
    -------
    (X, y_error, y_runtime) : (pd.DataFrame, pd.Series, pd.Series)
    """
    df = load_validation_analysis()

    if merge_runtime:
        df = _merge_runtime_from_log(df)

    if feature_cols is None:
        feature_cols = FEATURE_COLUMNS

    # Check that necessary columns exist
    missing_features = [c for c in feature_cols if c not in df.columns]
    missing_targets = [c for c in [error_col, runtime_col] if c not in df.columns]

    if missing_features:
        raise KeyError(
            f"Missing feature columns in validation_analysis_full.csv after merge: {missing_features}\n"
            f"Available columns are:\n{list(df.columns)}"
        )
    if missing_targets:
        raise KeyError(
            f"Missing target columns in validation_analysis_full.csv after merge: {missing_targets}\n"
            f"Available columns are:\n{list(df.columns)}"
        )

    # Diagnostics
    total_rows = len(df)
    non_na_error = df[error_col].notna().sum()
    non_na_runtime = df[runtime_col].notna().sum()
    both_non_na = df[error_col].notna() & df[runtime_col].notna()
    both_non_na_count = both_non_na.sum()

    print(f"[data_handler] Total rows in validation_analysis_full: {total_rows}")
    print(f"[data_handler] Rows with non-NaN {error_col:>15}: {non_na_error}")
    print(f"[data_handler] Rows with non-NaN {runtime_col:>15}: {non_na_runtime}")
    print(f"[data_handler] Rows with both non-NaN targets   : {both_non_na_count}")

    if drop_na_targets:
        df = df[both_non_na].copy()
        print(f"[data_handler] After drop_na_targets, rows kept: {len(df)}")
    else:
        print("[data_handler] drop_na_targets=False, keeping all rows.")

    X = df[feature_cols].copy()
    y_error = df[error_col].copy()
    y_runtime = df[runtime_col].copy()

    return X, y_error, y_runtime
