#!/usr/bin/env python3
"""
Make validation CSVs comparing SAM vs experiment.

Inputs (default paths, override with CLI args if you want):
  - Experimental data: validation_data.csv
  - SAM case report:   case_report.csv

Outputs:
  - validation_analysis_full.csv         (detailed per-run errors)
  - validation_analysis_paper_table.csv  (short paper-style table)
  - validation_analysis_summary.csv      (per-prefix “best” row, for other scripts)

Run like so :
    python make_validation_analysis.py \
  --exp_csv validation_data.csv \
  --case_csv case_report.csv \
  --out_dir validation_outputs

"""

import argparse
import pathlib
import re

import numpy as np
import pandas as pd


# ---------- Helpers ----------

PREFIX_TO_EXP_COLUMN = {
    "jsalt1": "Salt Test 1",
    "jsalt2": "Salt Test 2",
    "jsalt3": "Salt Test 3",
    "jsalt4": "Salt Test 4",
    # If you later add water cases, extend like:
    # "jwater1": "Water Test 1",
    # "jwater2": "Water Test 2",
}


def parse_nodes_mult(source_file: str) -> float:
    """
    Extract the nodes_mult factor from a filename like:
    'jsalt1_nodes_mult_by_24_csv.csv' -> 24

    Returns np.nan if pattern is not found.
    """
    m = re.search(r"nodes_mult_by_(\d+)_csv", str(source_file))
    if m:
        return int(m.group(1))
    return np.nan


def compute_errors_for_row(row, exp_df):
    """
    Given one SAM row and the experimental DataFrame,
    compute error metrics and return as a dict of new columns.

    Uses TP1, TP2, TP3, TP6 and delta_T (TP6-TP2).
    """
    prefix = row["prefixes"]

    if prefix not in PREFIX_TO_EXP_COLUMN:
        # No experimental mapping for this prefix -> skip
        return None

    exp_col = PREFIX_TO_EXP_COLUMN[prefix]

    # Locations we will compare explicitly
    sites = ["TP1", "TP2", "TP3", "TP6"]

    new_vals = {}

    # Per-TP errors
    diffs_sq = []
    abs_errs = []

    for site in sites:
        exp_val = float(exp_df.loc[site, exp_col])
        sam_val = float(row[site])

        diff = sam_val - exp_val
        abs_diff = abs(diff)
        rel_pct = diff / exp_val * 100.0 if exp_val != 0 else np.nan

        new_vals[f"exp_{site}"] = exp_val
        new_vals[f"sam_{site}"] = sam_val
        new_vals[f"err_{site}"] = diff
        new_vals[f"abs_err_{site}"] = abs_diff
        new_vals[f"rel_err_{site}_pct"] = rel_pct

        diffs_sq.append(diff**2)
        abs_errs.append(abs_diff)

    # RMSE and max abs error across TP1, TP2, TP3, TP6
    if diffs_sq:
        rmse = float(np.sqrt(np.mean(diffs_sq)))
        max_abs = float(np.max(abs_errs))
    else:
        rmse = np.nan
        max_abs = np.nan

    new_vals["rmse_K"] = rmse
    new_vals["max_abs_err_K"] = max_abs

    # Delta T (TP6 - TP2)
    exp_delta = float(exp_df.loc["TP6", exp_col] - exp_df.loc["TP2", exp_col])
    sam_delta = float(row["delta_Temp_TP6-TP2"])

    delta_diff = sam_delta - exp_delta
    delta_abs = abs(delta_diff)
    delta_rel_pct = delta_diff / exp_delta * 100.0 if exp_delta != 0 else np.nan

    new_vals["exp_delta_TP6_TP2"] = exp_delta
    new_vals["sam_delta_TP6_TP2"] = sam_delta
    new_vals["err_delta_TP6_TP2"] = delta_diff
    new_vals["abs_err_delta_TP6_TP2"] = delta_abs
    new_vals["rel_err_delta_TP6_TP2_pct"] = delta_rel_pct

    return new_vals


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp_csv",
        default="validation_data.csv",
        help="CSV with experimental data (Kelvin, Salt Test 1..4, Water Test 1..4)",
    )
    parser.add_argument(
        "--case_csv",
        default="case_report.csv",
        help="CSV with SAM case report (your big table)",
    )
    parser.add_argument(
        "--out_dir",
        default=".",
        help="Output directory for the generated CSV files",
    )
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Load experimental data ---
    # Expected format:
    #   Kelvin,Salt Test 1,Salt Test 2,Salt Test 3,Salt Test 4,Water Test 1,...
    #   TP1,449.37,453.26,465.81,481.34,314.03,...
    #   TP2,...
    exp_df = pd.read_csv(args.exp_csv)
    # Use 'Kelvin' labels (TP1, TP2, ...) as the index
    exp_df = exp_df.set_index("Kelvin")

    # --- Load case report data ---
    case_df = pd.read_csv(args.case_csv)

    # Keep only rows where reached_end_any is True
    # (skip failed/incomplete runs)
    if case_df["reached_end_any"].dtype == bool:
        good_mask = case_df["reached_end_any"]
    else:
        # In case it's "True"/"False" as strings
        good_mask = case_df["reached_end_any"].astype(str).str.lower() == "true"

    case_df = case_df[good_mask].copy()

    # Extract nodes_mult from source_file
    case_df["nodes_mult"] = case_df["source_file"].apply(parse_nodes_mult)

    # Drop rows without nodes_mult (if any)
    case_df = case_df.dropna(subset=["nodes_mult"])
    case_df["nodes_mult"] = case_df["nodes_mult"].astype(int)

    # --- Compute error metrics for each row ---
    all_rows = []
    for _, row in case_df.iterrows():
        extra = compute_errors_for_row(row, exp_df)
        if extra is None:
            # No experimental mapping for this prefix, just skip it.
            continue
        combined = dict(row)  # original fields
        combined.update(extra)  # add error metrics
        all_rows.append(combined)

    if not all_rows:
        raise RuntimeError("No rows could be matched to experimental data. Check prefix->column mapping.")

    full_df = pd.DataFrame(all_rows)

    # Sort nicely by prefix and nodes_mult
    full_df = full_df.sort_values(["prefixes", "nodes_mult"]).reset_index(drop=True)

    # --- Output 1: Full analysis CSV ---
    full_path = out_dir / "validation_analysis_full.csv"
    full_df.to_csv(full_path, index=False)
    print(f"Wrote full analysis to: {full_path}")

    # --- Output 2: Short paper-style table ---
    # Pick a reasonable subset of columns for a validation table
    paper_cols = [
        "prefixes",
        "nodes_mult",
        "source_file",
        "script_runtime",
        "rmse_K",
        "max_abs_err_K",
        "exp_TP2",
        "sam_TP2",
        "rel_err_TP2_pct",
        "exp_TP6",
        "sam_TP6",
        "rel_err_TP6_pct",
        "exp_delta_TP6_TP2",
        "sam_delta_TP6_TP2",
        "rel_err_delta_TP6_TP2_pct",
    ]

    paper_cols = [c for c in paper_cols if c in full_df.columns]  # safety
    paper_df = full_df[paper_cols].copy()

    paper_path = out_dir / "validation_analysis_paper_table.csv"
    paper_df.to_csv(paper_path, index=False)
    print(f"Wrote paper table to: {paper_path}")

    # --- Output 3: Summary for another script ---
    # For each prefix (jsalt1..4), take the row with minimum rmse_K
    summary_df = (
        full_df.sort_values(["prefixes", "rmse_K"])
        .groupby("prefixes", as_index=False)
        .first()
    )

    # Keep just a small set of columns as the "summary"
    summary_cols = [
        "prefixes",
        "nodes_mult",
        "source_file",
        "script_runtime",
        "rmse_K",
        "max_abs_err_K",
    ]
    summary_cols = [c for c in summary_cols if c in summary_df.columns]
    summary_df = summary_df[summary_cols].copy()

    summary_path = out_dir / "validation_analysis_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"Wrote summary to: {summary_path}")


if __name__ == "__main__":
    main()
