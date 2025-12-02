"""
optimizer_loop.py

SAM optimizer v0: surrogate-based recommender + optional auto-run.

This script can:

  1. "suggest" mode (default):
       - Load dataset (features + error + runtime) via data_handler.
       - Train surrogates (RandomForest) for error and runtime.
       - Sample candidate hyperparameters from CONFIG["hyperparams_space"].
       - Predict error + runtime for candidates.
       - Filter by runtime cap.
       - Print a ranked table of top candidates.

  2. "suggest_and_run" mode:
       - Do everything in "suggest" mode.
       - Take the top N feasible candidates.
       - For each:
           * Map ML feature 'nodes_mult' -> run-time hyperparam 'node_multiplier'.
           * Call run_sam_case(...) for one or more jsalt cases.
       - This gives a closed loop: learn from past runs, propose, then launch.

Usage (from active_development):

    # Just print suggestions:
    python -m sam_tuner.optimizer_loop --mode suggest --top-k 10

    # Suggest and then actually run the top 3 candidates for jsalt1 and jsalt2:
    python -m sam_tuner.optimizer_loop --mode suggest_and_run --top-k 10 --n-run 3 --cases jsalt1 jsalt2
"""

from __future__ import annotations

from itertools import product
from typing import List, Dict, Any, Tuple, Optional

import argparse
import numpy as np
import pandas as pd
import subprocess
from pathlib import Path


from .config import CONFIG
from .data_handler import (
    build_basic_dataset,
    FEATURE_COLUMNS,
    ERROR_COLUMN,
    RUNTIME_COLUMN_DEFAULT,
)
from .models import (
    fit_surrogates,
    predict_error_runtime,
    normalize_targets,
)
from .run_launcher import run_sam_case


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _default_feature_values(X: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute a reasonable default value for each feature column based on the
    training data. For now:

      - numeric columns  -> median
      - non-numeric cols -> mode (most frequent)

    These defaults are used for features that we are NOT actively scanning
    in the candidate grid (e.g. 'order' when we're only varying 'nodes_mult').
    """
    defaults: Dict[str, Any] = {}
    for col in X.columns:
        series = X[col]
        if series.dtype.kind in "biufc":  # numeric types
            defaults[col] = float(series.median())
        else:
            mode = series.mode()
            defaults[col] = mode.iloc[0] if not mode.empty else None
    return defaults


def _generate_candidates_from_config(X_train: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a candidate grid of hyperparameters, focusing on the features in
    FEATURE_COLUMNS and the ranges defined in CONFIG["hyperparams_space"].

    Strategy:
      - For now, we actively vary only 'nodes_mult' if present in the config.
      - All other features are held at a default value learned from X_train.

    This keeps the grid simple and avoids NaNs for features we're not tuning yet.
    """
    space = CONFIG["hyperparams_space"]
    defaults = _default_feature_values(X_train)

    feature_values: Dict[str, List[Any]] = {}

    for feat in FEATURE_COLUMNS:
        if feat == "nodes_mult" and feat in space:
            val = space[feat]
            if isinstance(val, (list, tuple)):
                feature_values[feat] = list(val)
            else:
                feature_values[feat] = [val]
        else:
            # Hold all other features (e.g. 'order') fixed at their default.
            feature_values[feat] = [defaults.get(feat)]

    keys = list(feature_values.keys())
    grids = list(product(*[feature_values[k] for k in keys]))

    rows = []
    for combo in grids:
        row = {k: v for k, v in zip(keys, combo)}
        rows.append(row)

    df_candidates = pd.DataFrame(rows)
    return df_candidates


def _compute_scores(
    err_norm: np.ndarray,
    rt_norm: np.ndarray,
) -> np.ndarray:
    """
    Combine normalized error and runtime into a scalar score using weights from CONFIG.

    Lower score is better.
    """
    w_err = float(CONFIG["objective_weights"]["error"])
    w_rt = float(CONFIG["objective_weights"]["runtime"])
    return w_err * err_norm + w_rt * rt_norm

def _project_root() -> Path:
    """
    Return the active_development root directory (one level above sam_tuner).
    Assumes this file is active_development/sam_tuner/optimizer_loop.py.
    """
    here = Path(__file__).resolve()
    return here.parent.parent


def _analysis_dir() -> Path:
    """
    Directory where csv_maker.py and csv_analysis.py live.
    Uses CONFIG['paths']['results_root'] (typically 'analysis') relative
    to the active_development root.
    """
    root = _project_root()
    results_root = Path(CONFIG["paths"]["results_root"])
    if not results_root.is_absolute():
        results_root = root / results_root
    return results_root


def _rerun_analysis_scripts() -> None:
    """
    Re-run csv_maker.py and csv_analysis.py so that any new SAM runs launched
    by suggest_and_run_mode are incorporated into validation_analysis_full.csv.
    """
    analysis_dir = _analysis_dir()
    csv_maker = analysis_dir / "csv_maker.py"
    csv_analysis = analysis_dir / "csv_analysis.py"

    if not csv_maker.exists():
        print(f"[suggest_and_run] WARNING: csv_maker.py not found in {analysis_dir}; "
              "skipping automatic analysis.")
        return
    if not csv_analysis.exists():
        print(f"[suggest_and_run] WARNING: csv_analysis.py not found in {analysis_dir}; "
              "skipping automatic analysis.")
        return

    print("\n[suggest_and_run] Re-running csv_maker.py to update case_report.csv...")
    subprocess.run(
        ["python", csv_maker.name],
        cwd=analysis_dir,
        check=True,
    )

    print("[suggest_and_run] Re-running csv_analysis.py to update validation_analysis_full.csv...")
    subprocess.run(
        ["python", csv_analysis.name],
        cwd=analysis_dir,
        check=True,
    )

    print("[suggest_and_run] Analysis scripts completed.\n")


# ---------------------------------------------------------------------------
# Core optimizer logic
# ---------------------------------------------------------------------------

def run_optimizer_v0(
    top_k: int = 10,
    return_df: bool = False,
) -> Tuple[Optional[pd.DataFrame], Optional[object]]:
    """
    Run the v0 optimizer:

      - Load dataset
      - Train surrogates
      - Generate candidates from CONFIG
      - Predict error + runtime for candidates
      - Filter by runtime cap
      - Rank by score and print top_k

    Parameters
    ----------
    top_k : int
        Number of best candidates to print.
    return_df : bool
        If True, return the full results DataFrame and the fitted models
        (for use in suggest_and_run). If False, just print and return (None, None).

    Returns
    -------
    (df_results, models) : (pd.DataFrame or None, SurrogateModels or None)
    """
    print("=== SAM Optimizer v0: Surrogate-based recommender ===")

    # 1) Load dataset (X, y_error, y_runtime)
    X, y_err, y_rt = build_basic_dataset(
        error_col=ERROR_COLUMN,
        runtime_col=RUNTIME_COLUMN_DEFAULT,
        drop_na_targets=True,
        merge_runtime=True,
    )

    print(f"[optimizer] Loaded dataset with {len(X)} rows.")

    if len(X) == 0:
        raise RuntimeError(
            "No data available with both error and runtime. "
            "Run some SAM sweeps, rerun csv_analysis.py, and try again."
        )

    # 2) Fit surrogates
    models = fit_surrogates(X, y_err, y_rt)

    # 3) Generate candidate hyperparams
    df_candidates = _generate_candidates_from_config(X)
    print(f"[optimizer] Generated {len(df_candidates)} candidate hyperparameter combos.")
    print(df_candidates.head())

    # 4) Predict error + runtime for candidates
    err_pred, rt_pred = predict_error_runtime(models, df_candidates)
    err_norm, rt_norm = normalize_targets(models, err_pred, rt_pred)

    # 5) Apply runtime cap
    runtime_cap = float(CONFIG["runtime_limits"]["absolute_sec"])
    feasible_mask = rt_pred <= runtime_cap
    num_feasible = int(feasible_mask.sum())

    print(f"[optimizer] Runtime cap: {runtime_cap:.2f} s")
    print(f"[optimizer] Feasible candidates (pred runtime <= cap): {num_feasible}/{len(df_candidates)}")

    if num_feasible == 0:
        print("[optimizer] WARNING: No candidates satisfy the runtime cap based on surrogate predictions.")
        # Still compute scores; treat all as 'feasible' for ranking purposes.
        feasible_mask = np.ones_like(rt_pred, dtype=bool)

    # 6) Compute scores and rank
    scores = _compute_scores(err_norm, rt_norm)

    df_results = df_candidates.copy()
    df_results["pred_error"] = err_pred
    df_results["pred_runtime"] = rt_pred
    df_results["err_norm"] = err_norm
    df_results["rt_norm"] = rt_norm
    df_results["score"] = scores
    df_results["feasible_runtime"] = feasible_mask

    # Sort: feasible first, then by score ascending
    df_results = df_results.sort_values(
        by=["feasible_runtime", "score"],
        ascending=[False, True],
    ).reset_index(drop=True)

    print("\n=== Top candidate hyperparameters (surrogate-based) ===")
    n_show = min(top_k, len(df_results))
    print(
        df_results.head(n_show)[
            FEATURE_COLUMNS
            + ["pred_error", "pred_runtime", "score", "feasible_runtime"]
        ]
    )

    print("\nInterpretation:")
    print("  - 'pred_error'   : surrogate-predicted error (e.g., RMSE in K).")
    print("  - 'pred_runtime' : surrogate-predicted runtime in seconds.")
    print("  - 'score'        : weighted combination of normalized error and runtime; lower is better.")
    print("  - 'feasible_runtime' : True if pred_runtime <= runtime cap.")

    if return_df:
        return df_results, models
    else:
        return None, None


# ---------------------------------------------------------------------------
# suggest_and_run mode
# ---------------------------------------------------------------------------

def suggest_and_run_mode(
    top_k_suggest: int = 10,
    n_run: int = 3,
    cases: Optional[List[str]] = None,
) -> None:
    """
    Run optimizer v0 to get suggestions, then actually launch SAM runs for
    the top N feasible candidates.

    Parameters
    ----------
    top_k_suggest : int
        Number of top candidates to consider when choosing runs.
    n_run : int
        Number of candidates to actually run (max; fewer if less feasible).
    cases : list of str or None
        List of case names (e.g. ["jsalt1", "jsalt2"]). If None, defaults
        to ["jsalt1"] for now.
    """
    if cases is None or len(cases) == 0:
        cases = ["jsalt1"]

    print("=== SAM Optimizer v0: suggest_and_run mode ===")
    print(f"[suggest_and_run] Cases to run: {cases}")
    print(f"[suggest_and_run] Will consider top {top_k_suggest} candidates and run up to {n_run} of them.")

    df_results, _models = run_optimizer_v0(top_k=top_k_suggest, return_df=True)

    if df_results is None or df_results.empty:
        print("[suggest_and_run] No optimizer results available.")
        return

    # Filter to feasible candidates by runtime, then take the first n_run
    feasible = df_results[df_results["feasible_runtime"]].copy()
    if feasible.empty:
        print("[suggest_and_run] No candidates satisfy the runtime cap; "
              "falling back to best overall candidates.")
        feasible = df_results.copy()

    feasible = feasible.reset_index(drop=True)
    n_actual = min(n_run, len(feasible))

    print(f"[suggest_and_run] Selected {n_actual} candidate(s) to run.")

    # Runtime cap to pass to run_sam_case (same as optimizer cap for now)
    runtime_cap = float(CONFIG["runtime_limits"]["absolute_sec"])

    for idx in range(n_actual):
        row = feasible.iloc[idx]
        nodes_mult = row.get("nodes_mult")

        print("\n--------------------------------------------------")
        print(f"[suggest_and_run] Candidate #{idx+1}:")
        print(row[FEATURE_COLUMNS + ["pred_error", "pred_runtime", "score"]])

        if pd.isna(nodes_mult):
            print("[suggest_and_run] WARNING: nodes_mult is NaN for this candidate; skipping.")
            continue

        # Map ML feature 'nodes_mult' -> run-time hyperparam 'node_multiplier'
        hyperparams = {
            "node_multiplier": int(nodes_mult),
            # TODO: when 'order' becomes a real feature in the CSV,
            #       map it here as well, e.g.:
            # "order": int(row["order"]),
        }

        for case in cases:
            template_name = f"{case}.i"
            print(f"[suggest_and_run] Launching SAM run for case={case}, template={template_name}, "
                  f"hyperparams={hyperparams}, timeout={runtime_cap:.1f}s")

            try:
                summary = run_sam_case(
                    case_name=case,
                    template_name=template_name,
                    hyperparams=hyperparams,
                    timeout_sec=runtime_cap,
                )
                print(f"[suggest_and_run] Run summary for {case}:")
                for k, v in summary.items():
                    print(f"  {k}: {v}")
            except Exception as e:
                print(f"[suggest_and_run] ERROR while running case={case}: {e}")
    # --- NEW: rerun analysis after launching new runs --------------------
    if n_actual > 0:
        _rerun_analysis_scripts()



# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="SAM optimizer v0 (surrogate-based suggester and optional auto-run)."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["suggest", "suggest_and_run"],
        default="suggest",
        help=(
            "Run mode:\n"
            "  'suggest'         : train surrogates and print ranked candidates.\n"
            "  'suggest_and_run' : suggest, then run the top N candidates.\n"
            "Default: suggest."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top candidates to display (and to consider in suggest_and_run).",
    )
    parser.add_argument(
        "--n-run",
        type=int,
        default=3,
        help="Number of candidates to actually run in 'suggest_and_run' mode.",
    )
    parser.add_argument(
        "--cases",
        nargs="*",
        default=None,
        help="Case names to run (e.g. jsalt1 jsalt2). If omitted, defaults to ['jsalt1'].",
    )

    args = parser.parse_args()

    if args.mode == "suggest":
        run_optimizer_v0(top_k=args.top_k, return_df=False)
    else:
        suggest_and_run_mode(
            top_k_suggest=args.top_k,
            n_run=args.n_run,
            cases=args.cases,
        )


if __name__ == "__main__":
    main()
