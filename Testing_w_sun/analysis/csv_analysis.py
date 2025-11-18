#!/usr/bin/env python3
"""
Make validation CSVs comparing SAM vs experiment.

Inputs (defaults are aligned with your repo layout):
  - Experimental data: Validation_Data/validation_data.csv
  - SAM case reports:
        /First_order_nm_nureth26_analysis/case_report.csv
        /second_order_nm_exp_nureth26_analysis/case_report.csv

Outputs (saved under analysis/ by default):
  - /validation_analysis_full.csv         (detailed per-run errors)
  - /validation_analysis_paper_table.csv  (short paper-style table)
  - /validation_analysis_summary.csv      (per-prefix “best” row)

Run like so (from physor2026_andrew/Testing_w_sun/analysis):
    python csv_analysis.py

[] Make sure to change so that you can more easily change default search to be specified, not ctrl f and replace /First_order_nm.... 

"""

import argparse, pathlib, re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   
import matplotlib.pyplot as plt 

# ---------- User "control panel" ----------

# Which output files to generate
write_paper = True
write_summary = True
make_plots = True 

# Which TP locations to compare between SAM and experiment
#       # Script will automatically compute exp_value, sam_value, error, abs_error, rel_error
COMPARISON_SITES = ["TS_vel"] # ["TP1", "TP2", "TP3", "TP6", "TS_vel", "massFlowRate"]  # add "TP4", "TP5" here as needed

csv_cases = ["analysis/coarse_first_order_nm_physor_not_nureth26_analysis/case_report.csv",
             "analysis/coarse_second_order_nm_nureth26_analysis/case_report.csv",
             "analysis/Fine_first_order_nm_nureth26_analysis/case_report.csv", 
             "analysis/Fine_second_order_nm_exp_nureth26_analysis/case_report.csv"]

# Diagnostics & column-selection toggles
# Turn these on/off or True/False to add/remove diagnostics from *all* outputs.
TOGGLE_TP_VALUES = True            # exp_TP1, sam_TP1, err_TP1, etc.
TOGGLE_DELTA_VALUES = True         # exp_delta_TP6_TP2, err_delta_TP6_TP2, etc.
TOGGLE_RMSE = True                 # rmse_K
TOGGLE_MAX_ABS = True              # max_abs_err_K

# If True, prints which columns were removed/kept when writing output files
VERBOSE_COLUMN_FILTERING = True


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

def filter_columns(df, paper=False):
    """Apply column toggles before writing outputs."""

    remove = []

    if not TOGGLE_TP_VALUES: # if turned off: 
        for site in ["TP1", "TP2", "TP3", "TP6"]:
            remove += [
                f"exp_{site}",
                f"sam_{site}",
                f"err_{site}",
                f"abs_err_{site}",
                f"rel_err_{site}_pct",
            ]

    if not TOGGLE_DELTA_VALUES:
        remove += [
            "exp_delta_TP6_TP2",
            "sam_delta_TP6_TP2",
            "err_delta_TP6_TP2",
            "abs_err_delta_TP6_TP2",
            "rel_err_delta_TP6_TP2_pct",
        ]

    if not TOGGLE_RMSE:
        remove.append("rmse_K")

    if not TOGGLE_MAX_ABS:
        remove.append("max_abs_err_K")

    # Remove columns only if they exist
    remove = [c for c in remove if c in df.columns]
    trimmed = df.drop(columns=remove, errors="ignore")

    if VERBOSE_COLUMN_FILTERING:
        print("\nColumn filter summary:")
        print("Removed:", remove)
        print("Remaining:", list(trimmed.columns))

    return trimmed

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


def infer_order_label(path: pathlib.Path) -> str:
    """
    Renames files. 
    Infer a clean 'order' label from the parent folder name, e.g.

      'analysis/coarse_first_order_nm_physor_not_nureth26_analysis'     -> 'First_order'
      'analysis/coarse_second_order_nm_nureth26_analysis'-> 'second_order'

    Falls back to the full parent name if no pattern is found.
    """
    parent_name = path.parent.name
    m = re.search(r"(first_order|second_order)", parent_name, re.IGNORECASE)
    if m:
        return m.group(1)  # 'First_order' or 'second_order' (as in the folder)
    return parent_name or "unknown_order"


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

    # Locations we will compare explicitly (from control panel)
    sites = COMPARISON_SITES


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

def make_convergence_plots(full_df, out_dir):
    """
    For each salt case (prefix jsalt1..4), make two plots:

      1) Signed relative error [%] vs nodes_mult
      2) Absolute relative error [%] vs nodes_mult

    Each plot overlays curves for:
      TP2, TP3, TP6, TS_vel, massFlowRate

    First/second order are both shown, distinguished by marker/linestyle.
    """
    import matplotlib.pyplot as plt

    plot_dir = out_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    # Metrics we care about
    metrics = ["TP2", "TP3", "TP6", "TS_vel", "massFlowRate"]

    # We expect columns like rel_err_TP2_pct, rel_err_TS_vel_pct, etc.
    prefixes = sorted(full_df["prefixes"].unique())

    # Simple mapping so first/second order look different in the plot
    order_styles = {
        "first_order": {"marker": "o", "linestyle": "-"},
        "second_order": {"marker": "s", "linestyle": "--"},
    }

    for prefix in prefixes:
        df_p = full_df[full_df["prefixes"] == prefix].copy()
        if df_p.empty:
            continue

        # Sort by nodes_mult so lines look like proper trendlines
        df_p = df_p.sort_values("nodes_mult")

        # ---- 1) Signed relative errors ----
        fig, ax = plt.subplots(figsize=(7, 5))

        for order in sorted(df_p["order"].unique()):
            df_po = df_p[df_p["order"] == order]
            if df_po.empty:
                continue

            style = order_styles.get(order, {"marker": "o", "linestyle": "-"})

            for metric in metrics:
                col = f"rel_err_{metric}_pct"
                if col not in df_po.columns:
                    continue

                x = df_po["nodes_mult"]
                y = df_po[col]

                # One "trendline" (connecting line) per metric
                label = f"{metric} ({order})"
                ax.plot(
                    x,
                    y,
                    marker=style["marker"],
                    linestyle=style["linestyle"],
                    label=label,
                )

        ax.axhline(0.0, linestyle=":", linewidth=0.8)
        ax.set_xlabel("nodes_mult")
        ax.set_ylabel("Relative error [%]")
        ax.set_title(f"{prefix}: signed relative errors vs mesh refinement")
        ax.legend(fontsize=7, ncol=2)
        fig.tight_layout()

        signed_path = plot_dir / f"{prefix}_rel_err_vs_nodes_mult.png"
        fig.savefig(signed_path, dpi=200)
        plt.close(fig)

        # ---- 2) Absolute relative errors ----
        fig, ax = plt.subplots(figsize=(7, 5))

        for order in sorted(df_p["order"].unique()):
            df_po = df_p[df_p["order"] == order]
            if df_po.empty:
                continue

            style = order_styles.get(order, {"marker": "o", "linestyle": "-"})

            for metric in metrics:
                col = f"rel_err_{metric}_pct"
                if col not in df_po.columns:
                    continue

                x = df_po["nodes_mult"]
                y = df_po[col].abs()

                label = f"{metric} ({order})"
                ax.plot(
                    x,
                    y,
                    marker=style["marker"],
                    linestyle=style["linestyle"],
                    label=label,
                )

        ax.set_xlabel("nodes_mult")
        ax.set_ylabel("Absolute relative error [%]")
        ax.set_yscale("log")

        ax.set_title(f"{prefix}: log(|relative error|) vs mesh refinement")
        ax.legend(fontsize=7, ncol=2)
        fig.tight_layout()

        abs_path = plot_dir / f"{prefix}_abs_rel_err_vs_nodes_mult.png"
        fig.savefig(abs_path, dpi=200)
        plt.close(fig)

        print(f"[PLOT] Saved for {prefix}:")
        print(f"       {signed_path}")
        print(f"       {abs_path}")



# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp_csv",
        default="Validation_Data/validation_data.csv",
        help="CSV with experimental data (Kelvin, Salt Test 1..4, Water Test 1..4)",
    )
    parser.add_argument(
        "--case_csv",
        nargs="+",
        default= csv_cases,
        help="One or more CSVs with SAM case reports (your big tables)",
    )
    parser.add_argument(
        "--out_dir",
        default="analysis",
        help="Output directory for the generated CSV files",
    )
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    #### --- Load experimental data --- #####
    exp_df = pd.read_csv(args.exp_csv)

    # Strip whitespace from column names
    exp_df.columns = exp_df.columns.str.strip()

    if "Kelvin" not in exp_df.columns:
        raise RuntimeError(
            f"Expected a 'Kelvin' column in {args.exp_csv}, got columns: {list(exp_df.columns)}"
        )

    # Strip whitespace from the Kelvin labels (TP1, TP2, ...)
    exp_df["Kelvin"] = exp_df["Kelvin"].astype(str).str.strip()

    # Use 'Kelvin' labels (TP1, TP2, ...) as the index
    exp_df = exp_df.set_index("Kelvin")

    # Make sure index is clean
    exp_df.index = exp_df.index.astype(str).str.strip()

    # Convert all data columns to numeric (coerce non-numerics / blanks to NaN)
    for col in exp_df.columns:
        exp_df[col] = pd.to_numeric(exp_df[col], errors="coerce")


    # --- Load and combine case report data ---
    case_frames = []
    for path_str in args.case_csv:
        path = pathlib.Path(path_str)
        df = pd.read_csv(path)

        # Tag with 'order' based on the parent folder name (e.g. 'First_order', 'second_order')
        df["order"] = infer_order_label(path)

        case_frames.append(df)

    if not case_frames:
        raise RuntimeError("No case_report CSVs were loaded. Check --case_csv paths.")

    case_df = pd.concat(case_frames, ignore_index=True)

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
        combined = dict(row)  # original fields (includes 'order')
        combined.update(extra)  # add error metrics
        all_rows.append(combined)

    if not all_rows:
        raise RuntimeError("No rows could be matched to experimental data. Check prefix->column mapping.")

    full_df = pd.DataFrame(all_rows)

    # Sort nicely by prefix, order, and nodes_mult
    sort_cols = [c for c in ["prefixes", "order", "nodes_mult"] if c in full_df.columns]
    full_df = full_df.sort_values(sort_cols).reset_index(drop=True)
    # ---- MAKE PLOTS (optional) ----
    if make_plots:
        make_convergence_plots(full_df, out_dir)


    # --- Output 1: Full analysis CSV ---
    
    full_path = out_dir / "validation_analysis_full.csv"
    full_df_out = filter_columns(full_df)
    full_df_out.to_csv(full_path, index=False)
    print(f"Wrote full analysis to: {full_path}")


    # --- Output 2: Short paper-style table ---
    if write_paper:
        paper_cols = [
            "prefixes",
            "order",         # see first_order vs second_order
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
        paper_df = filter_columns(paper_df, paper=True)
        
        paper_path = out_dir / "validation_analysis_paper_table.csv"
        paper_df.to_csv(paper_path, index=False)
        print(f"Wrote paper table to: {paper_path}")

    # --- Output 3: Summary for another script ---
    # For each prefix (jsalt1..4), take the row with minimum rmse_K across ALL orders
    if write_summary:

        summary_df = (
            full_df.sort_values(["prefixes", "rmse_K"])
            .groupby("prefixes", as_index=False)
            .first()
        )

        # Keep just a small set of columns as the "summary"
        summary_cols = [
            "prefixes",
            "order",        # which order produced the best row
            "nodes_mult",
            "source_file",
            "script_runtime",
            "rmse_K",
            "max_abs_err_K",
        ]
        summary_cols = [c for c in summary_cols if c in summary_df.columns]
        summary_df = summary_df[summary_cols].copy()
        summary_df = filter_columns(summary_df)

        summary_path = out_dir / "validation_analysis_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"Wrote summary to: {summary_path}")


if __name__ == "__main__":
    main()
