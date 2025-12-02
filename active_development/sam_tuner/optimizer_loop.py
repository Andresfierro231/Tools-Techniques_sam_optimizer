"""
optimizer_loop.py

Version 0 of the SAM optimizer loop.

This script:
  1. Loads the existing dataset (features + error + runtime) via data_handler.
  2. Trains surrogate models (RandomForest) for error and runtime.
  3. Samples candidate hyperparameter combinations from CONFIG["hyperparams_space"].
  4. Uses the surrogates to predict error and runtime for each candidate.
  5. Filters out candidates predicted to exceed the runtime cap.
  6. Computes a combined score:
        score = w_err * normalized_error + w_rt * normalized_runtime
     using weights from CONFIG["objective_weights"].
  7. Prints a ranked list of top candidates.

This version does NOT launch new SAM runs yet; it's a recommender based on
existing data. Later, we'll extend it to actually call run_sam_case() for
the best candidates and update the dataset.
"""

from __future__ import annotations

from itertools import product
from typing import List, Dict, Any

import numpy as np
import pandas as pd

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


def _generate_candidates_from_config() -> pd.DataFrame:
    """
    Generate a candidate grid of hyperparameters from CONFIG["hyperparams_space"],
    restricted to the feature columns used by the models.

    For now we only care about 'nodes_mult' and 'order' (from FEATURE_COLUMNS),
    but this function is written to be extensible: other hyperparams will simply
    be included if they appear in FEATURE_COLUMNS.
    """
    space = CONFIG["hyperparams_space"]

    # Mapping feature_names -> list of possible values
    feature_values: Dict[str, List[Any]] = {}

    for feat in FEATURE_COLUMNS:
        if feat in space:
            # Could be list (discrete) or tuple (continuous range)
            val = space[feat]
            if isinstance(val, (list, tuple)):
                if isinstance(val, tuple):
                    # For a continuous range, sample a small grid
                    lo, hi = float(val[0]), float(val[1])
                    # Example: 5 points
                    feature_values[feat] = list(np.linspace(lo, hi, num=5))
                else:
                    feature_values[feat] = list(val)
            else:
                feature_values[feat] = [val]
        else:
            # If the feature isn't explicitly in hyperparams_space, we can't
            # propose values for it; just leave it out for now.
            print(f"[optimizer] WARNING: feature {feat!r} not in hyperparams_space; "
                  f"candidates will have NaN for this column.")
            feature_values[feat] = [np.nan]

    # Cartesian product of all feature values
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
    score = w_err * err_norm + w_rt * rt_norm
    return score


def run_optimizer_v0(top_k: int = 10):
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
    df_candidates = _generate_candidates_from_config()
    print(f"[optimizer] Generated {len(df_candidates)} candidate hyperparameter combos.")
    print(df_candidates.head())

    # 4) Predict error + runtime for candidates
    err_pred, rt_pred = predict_error_runtime(models, df_candidates)
    err_norm, rt_norm = normalize_targets(models, err_pred, rt_pred)

    # 5) Apply runtime cap
    runtime_cap = float(CONFIG["runtime_limits"]["absolute_sec"])
    feasible_mask = rt_pred <= runtime_cap
    num_feasible = feasible_mask.sum()

    print(f"[optimizer] Runtime cap: {runtime_cap:.2f} s")
    print(f"[optimizer] Feasible candidates (pred runtime <= cap): {num_feasible}/{len(df_candidates)}")

    if num_feasible == 0:
        print("[optimizer] WARNING: No candidates satisfy the runtime cap based on surrogate predictions.")
        # We still proceed to print the best few by score overall.
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


def main():
    run_optimizer_v0(top_k=10)


if __name__ == "__main__":
    main()
