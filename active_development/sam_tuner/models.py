"""
models.py

Surrogate models for the SAM optimizer.

This module provides:
  - fit_surrogates(X, y_error, y_runtime): train regressors for error and runtime
  - predict_error_runtime(models, X_new): predict error and runtime for new designs
  - normalize_targets(): simple min-max scaling to [0, 1] for score computation

We use scikit-learn's RandomForestRegressor by default. The models are wrapped
in a small dataclass for convenience.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


@dataclass
class SurrogateModels:
    """Container for the two surrogate models and some metadata."""
    error_model: Pipeline
    runtime_model: Pipeline
    feature_columns: List[str]
    error_min: float
    error_max: float
    runtime_min: float
    runtime_max: float


def _build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """
    Build a ColumnTransformer that:
      - passes numeric columns through unchanged
      - one-hot encodes non-numeric (object/category) columns
    """
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    transformers = []
    if numeric_cols:
        transformers.append(("num", "passthrough", numeric_cols))
    if categorical_cols:
        transformers.append(
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_cols,
            )
        )

    if not transformers:
        raise ValueError("No columns found in X to preprocess.")

    preprocessor = ColumnTransformer(transformers)
    return preprocessor


def fit_surrogates(
    X: pd.DataFrame,
    y_error: pd.Series,
    y_runtime: pd.Series,
    n_estimators: int = 200,
    random_state: int = 42,
) -> SurrogateModels:
    """
    Fit two RandomForestRegressors:
      - one for error (y_error)
      - one for runtime (y_runtime)

    Both share the same preprocessing pipeline so we can handle numeric and
    categorical features consistently.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix (columns like nodes_mult, order, etc.).
    y_error : pd.Series
        Error target (e.g., rmse_K).
    y_runtime : pd.Series
        Runtime target (e.g., runtime_merged_sec).
    n_estimators : int
        Number of trees for the RandomForest.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    SurrogateModels
        Container with fitted models and normalization info.
    """
    # Drop rows with NaN targets, but keep as many as possible
    mask = y_error.notna() & y_runtime.notna()
    X_train = X[mask].copy()
    y_err_train = y_error[mask].copy()
    y_rt_train = y_runtime[mask].copy()

    if len(X_train) == 0:
        raise ValueError(
            "No rows with both non-NaN error and runtime to train surrogates. "
            "Check your data pipeline or relax filtering."
        )

    print(f"[models] Training surrogates on {len(X_train)} samples with features: {list(X.columns)}")

    preprocessor = _build_preprocessor(X_train)

    # Define models
    err_rf = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,
    )
    rt_rf = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state + 1,
        n_jobs=-1,
    )

    # Pipelines: preprocessor + model
    error_model = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("rf", err_rf),
        ]
    )
    runtime_model = Pipeline(
        steps=[
            ("pre", preprocessor),
            ("rf", rt_rf),
        ]
    )

    # Fit both
    error_model.fit(X_train, y_err_train)
    runtime_model.fit(X_train, y_rt_train)

    # Compute min/max for normalization
    err_min = float(y_err_train.min())
    err_max = float(y_err_train.max())
    rt_min = float(y_rt_train.min())
    rt_max = float(y_rt_train.max())

    print(f"[models] Error range   : [{err_min:.4g}, {err_max:.4g}]")
    print(f"[models] Runtime range : [{rt_min:.4g}, {rt_max:.4g}]")

    return SurrogateModels(
        error_model=error_model,
        runtime_model=runtime_model,
        feature_columns=list(X.columns),
        error_min=err_min,
        error_max=err_max,
        runtime_min=rt_min,
        runtime_max=rt_max,
    )


def predict_error_runtime(
    models: SurrogateModels,
    X_new: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict error and runtime for new candidate designs.

    Parameters
    ----------
    models : SurrogateModels
        Fitted surrogate models.
    X_new : pd.DataFrame
        New feature matrix (must have same columns as training X).

    Returns
    -------
    (err_pred, rt_pred) : (np.ndarray, np.ndarray)
        Predicted error and runtime for each row.
    """
    # Ensure columns align (order, presence)
    X_new = X_new[models.feature_columns].copy()

    err_pred = models.error_model.predict(X_new)
    rt_pred = models.runtime_model.predict(X_new)
    return np.asarray(err_pred), np.asarray(rt_pred)


def normalize_targets(
    models: SurrogateModels,
    err: np.ndarray,
    rt: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Min-max normalize error and runtime to [0, 1] using the training ranges
    stored in the SurrogateModels object.

    If max == min for a target, we just return zeros for that target.
    """
    def _norm(vals: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        if vmax <= vmin:
            return np.zeros_like(vals)
        return (vals - vmin) / (vmax - vmin)

    err_norm = _norm(err, models.error_min, models.error_max)
    rt_norm = _norm(rt, models.runtime_min, models.runtime_max)
    return err_norm, rt_norm
