"""
report_summary.py

Produce a human-readable summary of "best" SAM configurations per case,
based on the validation_analysis_full.csv table, with hyperparameters
merged from runtimes_master.csv (T_0, T_c, T_h, h_amb, etc. when available).

Output:
  - Prints a summary to stdout
  - Writes the same text to:
      <results_root>/analysis/validation_summary_report.txt
"""

from pathlib import Path
import json

import pandas as pd

from .config import CONFIG
from .data_handler import _results_root, load_runtime_log


def _build_hyperparam_table_from_runtime() -> pd.DataFrame | None:
    """
    Build a table of hyperparameters per input_basename by parsing
    'hyperparams_json' from runtimes_master.csv.

    Returns
    -------
    pd.DataFrame or None

    Columns include:
      - input_basename
      - any keys found in hyperparams_json (T_0, T_c, T_h, h_amb, etc.)
    """
    rt = load_runtime_log()
    if rt is None:
        print("[report_summary] No runtime log available; skipping hyperparam merge.")
        return None

    if "hyperparams_json" not in rt.columns:
        print("[report_summary] 'hyperparams_json' missing in runtime log; "
              "cannot build hyperparam table.")
        return None

    df = rt[["sam_input_path", "hyperparams_json"]].dropna().copy()
    if df.empty:
        print("[report_summary] Runtime log has no rows with hyperparams_json; "
              "skipping hyperparam merge.")
        return None

    # Derive input_basename from sam_input_path (e.g. jsalt1_nodes_mult_by_6_ord2.i)
    df["input_basename"] = df["sam_input_path"].astype(str).apply(
        lambda s: Path(s).name
    )

    # Parse hyperparams_json into columns
    def _parse_hp(s: str) -> dict:
        try:
            return json.loads(s)
        except Exception:
            return {}

    hp_dicts = df["hyperparams_json"].apply(_parse_hp)
    hp_df = pd.json_normalize(hp_dicts)

    df_hp = pd.concat([df[["input_basename"]], hp_df], axis=1)
    df_hp = df_hp.groupby("input_basename", as_index=False).first()

    print("[report_summary] Hyperparam table (head):")
    print(df_hp.head())

    return df_hp


def make_report(top_k: int = 3) -> None:
    """
    Build and print a summary of best configurations per case.

    Parameters
    ----------
    top_k : int
        Number of top configurations to list per case.
    """
    # Load validation_analysis_full.csv
    root = _results_root()
    val_path = root / "analysis" / "validation_analysis_full.csv"

    if not val_path.exists():
        raise FileNotFoundError(
            f"[report_summary] validation_analysis_full.csv not found at: {val_path}"
        )

    df = pd.read_csv(val_path)
    print(f"[report_summary] Loaded validation analysis: {val_path}")
    print(f"[report_summary] Shape: {df.shape}")

    # Merge hyperparams (T_0, T_c, T_h, h_amb, etc.) from runtimes_master.csv
    hp_table = _build_hyperparam_table_from_runtime()
    if hp_table is not None:
        # validation_analysis_full already has input_basename
        if "input_basename" not in df.columns:
            print("[report_summary] WARNING: 'input_basename' missing in validation CSV; "
                  "cannot merge hyperparameters.")
        else:
            df = df.merge(hp_table, on="input_basename", how="left")
            print("[report_summary] After hyperparam merge, columns are:")
            print(df.columns.tolist())
    else:
        print("[report_summary] No hyperparams merged; proceeding with what we have.")

    # Ensure runtime column is present
    if "runtime_merged_sec" not in df.columns:
        # Fall back to any runtime_merged_sec_x/y if present
        for cand in ["runtime_merged_sec_x", "runtime_merged_sec_y", "script_runtime"]:
            if cand in df.columns:
                df["runtime_merged_sec"] = df[cand]
                print(f"[report_summary] INFO: using '{cand}' as runtime_merged_sec.")
                break

    # Keep only rows with valid error + runtime
    df = df.dropna(subset=["rmse_K", "runtime_merged_sec"])
    print(f"[report_summary] Rows with valid rmse_K & runtime: {len(df)}")

    if df.empty:
        print("[report_summary] No valid rows to summarize.")
        return

    # Simple scalar score: score = w_err * norm(error) + w_rt * norm(runtime)
    w_err = CONFIG["objective_weights"]["error"]
    w_rt = CONFIG["objective_weights"]["runtime"]

    df["err_norm"] = (df["rmse_K"] - df["rmse_K"].min()) / (
        (df["rmse_K"].max() - df["rmse_K"].min()) or 1.0
    )
    df["rt_norm"] = (df["runtime_merged_sec"] - df["runtime_merged_sec"].min()) / (
        (df["runtime_merged_sec"].max() - df["runtime_merged_sec"].min()) or 1.0
    )
    df["score"] = w_err * df["err_norm"] + w_rt * df["rt_norm"]

    # Columns we *would like* to show, but only use those that actually exist
    desired_cols = ["nodes_mult", "h_amb", "T_0", "T_c", "T_h",
                    "rmse_K", "runtime_merged_sec", "score"]
    available_cols = [c for c in desired_cols if c in df.columns]

    lines: list[str] = []
    for prefix, group in df.groupby("prefixes"):
        lines.append(f"\n=== Case: {prefix} ===")

        best_err = group.nsmallest(top_k, "rmse_K")[available_cols]
        lines.append("Best by RMSE:")
        lines.append(best_err.to_string(index=False))

        best_score = group.nsmallest(top_k, "score")[available_cols]
        lines.append("\nBest by combined score (error + runtime):")
        lines.append(best_score.to_string(index=False))
        lines.append("")

    report_text = "\n".join(lines)
    out_path = root / "analysis" / "validation_summary_report.txt"
    out_path.write_text(report_text)

    print(report_text)
    print(f"\n[REPORT] Saved to {out_path}")


def main():
    make_report(top_k=3)


if __name__ == "__main__":
    main()
