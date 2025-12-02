#!/usr/bin/env python3
"""
    Make validation CSVs comparing SAM vs experiment. Or SAM against finely refined versions of SAM 

    Inputs (defaults are aligned with your repo layout):
    - Experimental data: ../Validation_Data/validation_data.csv
    - SAM case reports:
            /First_order_nm_nureth26_analysis/case_report.csv
            /second_order_nm_exp_nureth26_analysis/case_report.csv

    Outputs (saved under analysis/ by default):
    - /validation_analysis_full.csv         (detailed per-run errors)
    - /validation_analysis_paper_table.csv  (short paper-style table)
    - /validation_analysis_summary.csv      (per-prefix “best” row)

    Run like so (from physor2026_andrew/Testing_w_sun/analysis):
        python csv_analysis.py

    [] Fix issue with compilation of source documents: https://chatgpt.com/c/691cc205-fbe4-8331-816d-29e8d43973da 

"""

import argparse, pathlib, re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   
from matplotlib.ticker import MaxNLocator, NullLocator
import matplotlib.pyplot as plt 

# ---------- User "control panel" ----------

# Which output files to generate
write_paper = True
write_summary = True
make_plots = False 

# Which TP locations to compare between SAM and experiment
#       # Script will automatically compute exp_value, sam_value, error, abs_error, rel_error
COMPARISON_SITES = ["TP1", "TP2", "TP3", "TP6", "TS_vel"] #  "massFlowRate"]  # ["TS_vel"] # add "TP4", "TP5" here as needed

csv_cases = ["analysis/temp_test_analysis/case_report.csv"]
            #  "analysis/coarse_second_order_nm_nureth26_analysis/case_report.csv",
            #  "analysis/Fine_first_order_nm_nureth26_analysis/case_report.csv", 
            #  "analysis/Fine_second_order_nm_exp_nureth26_analysis/case_report.csv"]

# Diagnostics & column-selection toggles
# Turn these on/off or True/False to add/remove diagnostics from *all* outputs.
TOGGLE_TP_VALUES = True            # exp_TP1, sam_TP1, err_TP1, etc.
TOGGLE_DELTA_VALUES = True         # exp_delta_TP6_TP2, err_delta_TP6_TP2, etc.
TOGGLE_RMSE = True                 # rmse_K
TOGGLE_MAX_ABS = True              # max_abs_err_K

# Error mode:
#   "exp"                  -> compare against experimental data
#   "self_ref"             -> compare each (prefix, order) vs its own finest mesh
#   "self_ref_second_order"-> compare all runs vs finest *second-order* SAM per prefix
ERROR_MODE = "self_ref"   # "exp" or "self_ref" or "self_ref_second_order"



Debug = [ #"Long", 
         "tracking_cols_keeping",
        #  "infer_order_debug",
        #  "col_filter", # If True, prints which columns were removed/kept when writing output files
        ]

# ---- MAC NODES Plot refinement caps ----
# Global cap on nodes_mult for plotting (None = no cap)
MAX_NODES_GLOBAL = 45 # 30 # None      # or None if you don't want a global cap
# Optional per-prefix cap (overrides global for that prefix if present # Example: only jsalt1 up to 30, others unlimited
MAX_NODES_BY_PREFIX = {
    # "jsalt1": 30,      "jsalt2": 20,     "jsalt3": None,    "jsalt4": 30,
}

############### Selecting output for summaries and csv ########################
#           ##           ##           ##           ##           ##            # Outputs can be: case,source_file,reached_end_any,last_time,matched_end_time,prefixes,script_runtime,    TP1,TP2,TP3,TP6,    ref_TS_vel,sam_TS_vel,err_TS_vel,abs_err_TS_vel,rel_err_TS_vel_pct,     rmse_K,max_abs_err_K,   massFlowRate,order,nodes_mult,ref_TP1,sam_TP1,err_TP1,abs_err_TP1,rel_err_TP1_pct,ref_TP2,sam_TP2,err_TP2,abs_err_TP2,rel_err_TP2_pct,ref_TP3,sam_TP3,err_TP3,abs_err_TP3,rel_err_TP3_pct,ref_TP6,sam_TP6,err_TP6,abs_err_TP6,rel_err_TP6_pct,    TP_TS,TS_vel,TopL_velocity,delta_Temp_TP6-TP2,downcomer_out_velocity,   ref_delta_TP6_TP2,sam_delta_TP6_TP2,err_delta_TP6_TP2,abs_err_delta_TP6_TP2,rel_err_delta_TP6_TP2_pct
# For the summaries and outputs
#       Summary is used for the validation of the most refined run and the experimental data when in error mode self_ref*

SUMMARY_COLS = [
    "prefixes",
    "order",
    "nodes_mult",
    # "source_file",
    "script_runtime",
    "rmse_K",
    "max_abs_err_K",

    # comparison quantities (SAM vs reference or SAM vs experiment)
    "ref_TP2","sam_TP2",
    "rel_err_TP2_pct",

    "ref_TP6", "sam_TP6",
    "rel_err_TP6_pct",

    "ref_TS_vel", "sam_TS_vel", 
    "rel_err_TS_vel_pct",
]
PAPER_COLS = [
    # "reached_end_any", # always true
    "prefixes",
    "order",         # see first_order vs second_order
    "nodes_mult",
    "source_file",
    "script_runtime",
    "rmse_K",
    "max_abs_err_K",
    "ref_TP2",
    "sam_TP2",
    "rel_err_TP2_pct",
    "ref_TP6",
    "sam_TP6",
    "rel_err_TP6_pct",
    # "ref_delta_TP6_TP2",
    # "sam_delta_TP6_TP2",
    # "rel_err_delta_TP6_TP2_pct",
]


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

    if not TOGGLE_TP_VALUES:
        for site in ["TP1", "TP2", "TP3", "TP6"]:
            remove += [
                f"ref_{site}",
                f"sam_{site}",
                f"err_{site}",
                f"abs_err_{site}",
                f"rel_err_{site}_pct",
            ]

    if not TOGGLE_DELTA_VALUES:
        remove += [
            "ref_delta_TP6_TP2",
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

    if "col_filter" in Debug:
        print("\nColumn filter summary:")
        print("Removed:", remove)
        print("Remaining:", list(trimmed.columns))

    return trimmed


def parse_nodes_mult(source_file: str) -> float:
    """
    Extract the nodes_mult factor from a filename.

    Handles filenames like:
      - 'jsalt1_nodes_mult_by_24_csv.csv'
      - 'jsalt1_nodes_mult_by_24_ord2_csv.csv'

    Returns np.nan if the pattern is not found.
    """
    import re
    import numpy as np

    s = str(source_file)
    # Look for 'nodes_mult_by_<number>' anywhere in the filename
    m = re.search(r"nodes_mult_by_(\d+)", s)
    if m:
        return int(m.group(1))
    return np.nan


def infer_order_label(path: pathlib.Path) -> str:
    """
    Infer a clean 'order' label from the parent folder name, e.g.

      'analysis/coarse_first_order_nm_physor_not_nureth26_analysis'  -> 'first_order'
      'analysis/Fine_second_order_nm_nureth26_analysis'              -> 'second_order'

    Always returns 'first_order' or 'second_order' in lowercase if found.
    Falls back to the full parent name if no pattern is found.
    """
    parent_name = path.parent.name
    m = re.search(r"(first_order|second_order)", parent_name, re.IGNORECASE)
    if m:
        return m.group(1).lower()   # <-- normalize to 'first_order' or 'second_order'
    return parent_name or "unknown_order"

def build_reference_table(case_df, mode):
    """
    Build a reference table for SAM-based reference modes.

    mode == "self_ref":
        Reference is the finest mesh for *each (prefixes, order)*.
        ref_map key: (prefixes, order)

    mode == "self_ref_second_order":
        Reference is the finest mesh among rows with order == "second_order"
        for each prefix.
        ref_map key: prefix (string)
    """
    if "nodes_mult" not in case_df.columns:
        raise RuntimeError("nodes_mult column not present when building reference table.")

    ref_map = {}

    if mode == "self_ref":
        grouped = case_df.groupby(["prefixes", "order"])

        for (prefix, order), grp in grouped:
            idx = grp["nodes_mult"].idxmax()
            ref_row = grp.loc[idx]

            entry = {}
            for site in COMPARISON_SITES:
                entry[site] = float(ref_row[site])

            entry["delta_T"] = float(ref_row["delta_Temp_TP6-TP2"])
            ref_map[(prefix, order)] = entry

    elif mode == "self_ref_second_order":
        # Only second-order rows
        df_second = case_df[case_df["order"] == "second_order"].copy()
        grouped = df_second.groupby("prefixes", dropna=False)

        for prefix, grp in grouped:
            idx = grp["nodes_mult"].idxmax()
            ref_row = grp.loc[idx]

            entry = {}
            for site in COMPARISON_SITES:
                entry[site] = float(ref_row[site])

            entry["delta_T"] = float(ref_row["delta_Temp_TP6-TP2"])
            ref_map[prefix] = entry

    else:
        raise ValueError(f"build_reference_table: unsupported mode {mode}")

    return ref_map

def compute_errors_for_row(row, exp_df=None, ref_map=None, mode="exp"):
    """
    Given one SAM row, compute error metrics and return as a dict of new columns.

    mode == "exp":
        - Uses experimental DataFrame exp_df via PREFIX_TO_EXP_COLUMN.
        - "ref_*" columns correspond to experimental values.

    mode == "self_ref":
        - Uses reference SAM from ref_map[(prefix, order)],
          where that reference is the highest nodes_mult for that (prefix, order).

    mode == "self_ref_second_order":
        - Uses reference SAM from ref_map[prefix],
          where reference is highest nodes_mult among second-order runs for that prefix.

    In all modes:
        - ref_* is the reference value (experiment or SAM).
        - sam_* is the current row.
        - We compute per-site errors for COMPARISON_SITES,
          plus RMSE, max_abs_err, and delta_T (TP6-TP2) errors.
    """
    prefix = row["prefixes"]

    # ---- Pick reference values depending on mode ----
    if mode == "exp":
        if prefix not in PREFIX_TO_EXP_COLUMN:
            return None
        if exp_df is None:
            raise RuntimeError("exp_df is None but ERROR_MODE == 'exp'.")

        exp_col = PREFIX_TO_EXP_COLUMN[prefix]

        def get_ref_site_value(site):
            return float(exp_df.loc[site, exp_col])

        ref_delta_T = float(exp_df.loc["TP6", exp_col] - exp_df.loc["TP2", exp_col])

    elif mode == "self_ref":
        if ref_map is None:
            raise RuntimeError("ref_map is None but ERROR_MODE == 'self_ref'.")
        key = (row["prefixes"], row["order"])
        if key not in ref_map:
            return None

        ref_entry = ref_map[key]

        def get_ref_site_value(site):
            return float(ref_entry[site])

        ref_delta_T = float(ref_entry["delta_T"])

    elif mode == "self_ref_second_order":
        if ref_map is None:
            raise RuntimeError("ref_map is None but ERROR_MODE == 'self_ref_second_order'.")
        if prefix not in ref_map:
            # No second-order reference for this prefix
            return None

        ref_entry = ref_map[prefix]

        def get_ref_site_value(site):
            return float(ref_entry[site])

        ref_delta_T = float(ref_entry["delta_T"])

    else:
        raise ValueError(f"Unknown error mode: {mode}")

    # ---- Core error calculations ----
    sites = COMPARISON_SITES
    new_vals = {}

    diffs_sq = []
    abs_errs = []

    for site in sites:
        ref_val = get_ref_site_value(site)     # experiment or SAM reference
        sam_val = float(row[site])

        diff = sam_val - ref_val
        abs_diff = abs(diff)
        rel_pct = diff / ref_val * 100.0 if ref_val != 0 else np.nan

        new_vals[f"ref_{site}"] = ref_val
        new_vals[f"sam_{site}"] = sam_val
        new_vals[f"err_{site}"] = diff
        new_vals[f"abs_err_{site}"] = abs_diff
        new_vals[f"rel_err_{site}_pct"] = rel_pct

        diffs_sq.append(diff**2)
        abs_errs.append(abs_diff)

    # RMSE and max abs error across COMPARISON_SITES
    if diffs_sq:
        rmse = float(np.sqrt(np.mean(diffs_sq)))
        max_abs = float(np.max(abs_errs))
    else:
        rmse = np.nan
        max_abs = np.nan

    new_vals["rmse_K"] = rmse
    new_vals["max_abs_err_K"] = max_abs

    # Delta T (TP6 - TP2) errors
    sam_delta = float(row["delta_Temp_TP6-TP2"])

    delta_diff = sam_delta - ref_delta_T
    delta_abs = abs(delta_diff)
    delta_rel_pct = delta_diff / ref_delta_T * 100.0 if ref_delta_T != 0 else np.nan

    new_vals["ref_delta_TP6_TP2"] = ref_delta_T
    new_vals["sam_delta_TP6_TP2"] = sam_delta
    new_vals["err_delta_TP6_TP2"] = delta_diff
    new_vals["abs_err_delta_TP6_TP2"] = delta_abs
    new_vals["rel_err_delta_TP6_TP2_pct"] = delta_rel_pct

    return new_vals

def compute_exp_errors_for_row(row, exp_df):
    """
    Compute SAM-vs-experiment error metrics for a single row.

    This ignores ERROR_MODE and always uses experimental data via PREFIX_TO_EXP_COLUMN.
    Outputs columns named exp_*, sam_*, err_*, abs_err_*, rel_err_*_pct,
    plus delta-T metrics and rmse_K / max_abs_err_K.
    """
    prefix = row["prefixes"]

    if prefix not in PREFIX_TO_EXP_COLUMN:
        # No experimental mapping for this prefix -> skip
        return None

    exp_col = PREFIX_TO_EXP_COLUMN[prefix]
    sites = COMPARISON_SITES

    new_vals = {}
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

    # RMSE and max abs error across COMPARISON_SITES
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

def get_nodes_cap_for_prefix(prefix: str):
    """
    Return the effective nodes_mult cap for a given prefix.

    Priority:
      1) MAX_NODES_BY_PREFIX[prefix] if defined (even if None)
      2) MAX_NODES_GLOBAL if not None
      3) None (no cap)
    """
    if MAX_NODES_BY_PREFIX and prefix in MAX_NODES_BY_PREFIX:
        return MAX_NODES_BY_PREFIX[prefix]
    return MAX_NODES_GLOBAL


def make_convergence_plots(full_df, out_dir, max_nodes_global=None, max_nodes_by_prefix=None):
    """
    For each salt case (prefix jsalt1..4), make two plots:

      1) Signed relative error [%] vs nodes_mult
      2) Absolute relative error [%] vs nodes_mult

    Each plot overlays curves for:
      TP2, TP3, TP6, TS_vel, massFlowRate

    First/second order are both shown, distinguished by marker/linestyle.

    This version is defensive:
    - Skips prefixes with no rows.
    - Skips prefixes where nodes_mult is entirely NaN.
    - Skips orders (1/2) that have no data for that prefix.
    """
    import os

    if full_df is None or full_df.empty:
        print("[RUNTIME PLOT] full_df is empty; skipping runtime plots.")
        return

    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)
    prefixes = sorted(full_df["prefixes"].dropna().unique())

    for prefix in prefixes:
        df_p = full_df[full_df["prefixes"] == prefix].copy()
        if df_p.empty:
            print(f"[RUNTIME PLOT] Skipping prefix {prefix!r}: no rows.")
            continue

        # Drop NaNs in nodes_mult and runtime
        if "nodes_mult" not in df_p.columns:
            print(f"[RUNTIME PLOT] Skipping prefix {prefix!r}: no 'nodes_mult' column.")
            continue
        if "script_runtime" not in df_p.columns:
            print(f"[RUNTIME PLOT] Skipping prefix {prefix!r}: no 'script_runtime' column.")
            continue

        df_p = df_p.dropna(subset=["nodes_mult", "script_runtime"])
        if df_p.empty:
            print(f"[RUNTIME PLOT] Skipping prefix {prefix!r}: no valid nodes_mult/runtime rows.")
            continue

        # Optional: respect max_nodes settings if provided
        nodes_series = df_p["nodes_mult"]
        if max_nodes_by_prefix is not None and prefix in max_nodes_by_prefix:
            max_nodes_prefix = max_nodes_by_prefix[prefix]
        else:
            max_nodes_prefix = max_nodes_global

        if max_nodes_prefix is not None:
            df_p = df_p[df_p["nodes_mult"] <= max_nodes_prefix]
            if df_p.empty:
                print(
                    f"[RUNTIME PLOT] Skipping prefix {prefix!r}: "
                    f"no rows after applying max_nodes={max_nodes_prefix}."
                )
                continue
            nodes_series = df_p["nodes_mult"]

        # Now safe to compute min/max
        nodes_series = nodes_series.dropna()
        if nodes_series.empty:
            print(f"[RUNTIME PLOT] Skipping prefix {prefix!r}: nodes_mult is empty after filtering.")
            continue

        xmin = int(nodes_series.min())
        xmax = int(nodes_series.max())

        # Split by order if the column exists, otherwise treat as a single group
        if "order" in df_p.columns:
            df_ord1 = df_p[df_p["order"] == 1]
            df_ord2 = df_p[df_p["order"] == 2]
        else:
            df_ord1 = df_p
            df_ord2 = df_p.iloc[0:0]  # empty

        import matplotlib.pyplot as plt

        plt.figure()
        has_any = False

        if not df_ord1.empty:
            has_any = True
            plt.plot(
                df_ord1["nodes_mult"],
                df_ord1["script_runtime"],
                marker="o",
                linestyle="-",
                label="order 1",
            )
        if not df_ord2.empty:
            has_any = True
            plt.plot(
                df_ord2["nodes_mult"],
                df_ord2["script_runtime"],
                marker="s",
                linestyle="--",
                label="order 2",
            )

        if not has_any:
            plt.close()
            print(f"[RUNTIME PLOT] Skipping prefix {prefix!r}: no data for any order.")
            continue

        plt.xlabel("nodes_mult")
        plt.ylabel("script_runtime [s]")
        plt.title(f"Runtime vs nodes_mult for {prefix}")
        plt.legend()
        plt.xlim(xmin, xmax)

        out_path = os.path.join(out_dir, "plots", f"{prefix}_runtime_vs_nodes_mult.png")
        plt.savefig(out_path, bbox_inches="tight")
        plt.close()

        print(f"[PLOT] Saved runtime plot for {prefix}:")
        print(f"       {out_path}")


def make_runtime_plots(full_df, out_dir, max_nodes_global=None, max_nodes_by_prefix=None):
    """
    For each salt case (prefix jsalt1..4), make ONE runtime plot per prefix:

        jsaltX_runtime_vs_nodes_mult.png

    The plot shows script_runtime [s] vs nodes_mult with BOTH orders overlain.
    The x-axis is shared for both orders, but we do NOT artificially
    truncate to the min(max(nodes_mult)) of each order; only the user caps
    (global/per-prefix) are applied.
    """
    plot_dir = out_dir / "plots" / "Runtime_plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    if "script_runtime" not in full_df.columns:
        print("[RUNTIME PLOTS] 'script_runtime' column not found, skipping runtime plots.")
        return

    prefixes = sorted(full_df["prefixes"].unique())

    # Marker styles (can tweak if you like)
    order_styles = {
        "first_order":  {"marker": "o", "linestyle": "-",  "label": "1st order"},
        "second_order": {"marker": "s", "linestyle": "--", "label": "2nd order"},
    }

    for prefix in prefixes:
        df_p = full_df[full_df["prefixes"] == prefix].copy()
        if df_p.empty:
            continue

        # ---- 1) Apply global/per-prefix cap on nodes_mult (ONLY user caps) ----
        cap = None
        if max_nodes_by_prefix and prefix in max_nodes_by_prefix:
            cap = max_nodes_by_prefix[prefix]
        elif max_nodes_global is not None:
            cap = max_nodes_global

        if cap is not None:
            df_p = df_p[df_p["nodes_mult"] <= cap].copy()
            if df_p.empty:
                continue

        # Sort once by nodes_mult
        df_p = df_p.sort_values("nodes_mult")

        fig, ax = plt.subplots(figsize=(7, 5))

        # ---- 2) Plot both orders overlain on same axes ----
                
        # --- Defensive fix: ensure script_runtime is numeric ---
        if "script_runtime" in df_p.columns:
            df_p["script_runtime"] = pd.to_numeric(df_p["script_runtime"], errors="coerce")
            df_p = df_p.dropna(subset=["script_runtime"])

        for order, df_po in df_p.groupby("order"):
            if df_po.empty:
                continue

            style = order_styles.get(order, {"marker": "o", "linestyle": "-", "label": order})

            x = df_po["nodes_mult"]
            y = df_po["script_runtime"]

            ax.plot(
                x,
                y,
                marker=style["marker"],
                markersize=5,
                linestyle=style["linestyle"],
                label=style["label"],
            )

        # integer ticks, no minor ticks
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_minor_locator(NullLocator())

        # optional: explicitly set limits with a little padding
        xmin = int(df_p["nodes_mult"].min())
        xmax = int(df_p["nodes_mult"].max())
        ax.set_xlim(xmin - 0.5, xmax + 0.5)

        ax.set_xlabel("nodes_mult")
        ax.set_ylabel("Script runtime [s]")
        ax.set_title(f"{prefix}: runtime vs mesh refinement\n{ERROR_MODE}")
        ax.legend(fontsize=8)

        fig.tight_layout()
        out_path = plot_dir / f"{prefix}_runtime_vs_nodes_mult.png"
        fig.savefig(out_path, dpi=200)
        plt.close(fig)

        print(f"[PLOT] Saved runtime plot (overlaid orders): {out_path}")



# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp_csv",
        default="../../Validation_Data/validation_data.csv",
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

    #### --- Load experimental data (if needed) --- #####
    if ERROR_MODE == "exp":
        exp_df = pd.read_csv(args.exp_csv)

        # Strip whitespace from column names
        exp_df.columns = exp_df.columns.str.strip()

        if "Kelvin" not in exp_df.columns:
            raise RuntimeError(
                f"Expected a 'Kelvin' column in {args.exp_csv}, got columns: {list(exp_df.columns)}"
            )

        exp_df["Kelvin"] = exp_df["Kelvin"].astype(str).str.strip()
        exp_df = exp_df.set_index("Kelvin")
        exp_df.index = exp_df.index.astype(str).str.strip()

        for col in exp_df.columns:
            exp_df[col] = pd.to_numeric(exp_df[col], errors="coerce")
    else:
        exp_df = None


    # --- Load and combine case report data ---
    # --- Load and combine case report data ---
    case_frames = []
    for path_str in args.case_csv:
        path = pathlib.Path(path_str)
        df = pd.read_csv(path)

        # 1) Strip whitespace from column names
        df.columns = df.columns.str.strip()

        if "tracking_cols_keeping" in Debug:        
            print("\n--- LOADED FILE:", path_str, "---")
            print(df.columns.tolist())
            print("Num rows:", len(df))

        # 2) Strip whitespace from critical string columns if they exist
        for col in ["case", "source_file", "prefixes", "reached_end_any"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # 3) FIX DUPLICATE COLUMNS (if any)
        if df.columns.duplicated().any():
            new_cols = []
            seen = {}
            for col in df.columns:
                if col not in seen:
                    seen[col] = 0
                    new_cols.append(col)
                else:
                    seen[col] += 1
                    new_cols.append(f"{col}.{seen[col]}")
            df.columns = new_cols

        # 4) Tag with 'order' based on parent folder name
        df["order"] = infer_order_label(path)

        # 5) Save this frame
        case_frames.append(df)


    if not case_frames:
        raise RuntimeError("No case_report CSVs were loaded. Check --case_csv paths.")

    ### ----- Building case_df ----- ###

    case_df = pd.concat(case_frames, ignore_index=True)
    # Normalize prefixes once again (just in case)
    if "prefixes" in case_df.columns:
        case_df["prefixes"] = case_df["prefixes"].astype(str).str.strip()


    # Extract nodes_mult from source_file
    case_df["nodes_mult"] = case_df["source_file"].apply(parse_nodes_mult)

    # Saving full to file
    debug_path = out_dir / "full_cases.csv"
    case_df.to_csv(debug_path, index=False)

    if "tracking_cols_keeping" in Debug:
        # ---------- DEBUG BLOCK 1 ----------
        print("\nDEBUG BEFORE reached_end_any FILTER:")
        print("Second-order nodes_mult available (raw CSVs):")
        debug_before = (
            case_df[case_df["order"] == "second_order"]
                .groupby("prefixes")["nodes_mult"]
        )

        # Print min, max, and how many unique values per prefix
        print("  min / max / nunique by prefix:")
        print(debug_before.agg(['min', 'max', 'nunique']))

        # Print the full sorted unique list per prefix (no '...')
        print("\n  full unique nodes_mult by prefix:")
        print(debug_before.apply(lambda s: sorted(s.unique())))
        print("---------------------------------------")
        # -----------------------------------------


    # Keep only rows where reached_end_any is True
    # (skip failed/incomplete runs)
    if case_df["reached_end_any"].dtype == bool:
        good_mask = case_df["reached_end_any"]
    else:
        # Robust: handle "True", " true ", "TRUE", etc.
        good_mask = (
            case_df["reached_end_any"]
            .astype(str).str.strip().str.lower() == "true"
        )

    case_df = case_df[good_mask].copy()

    if "tracking_cols_keeping" in Debug: 
        # ---------- DEBUG BLOCK 2 ----------
        print("\nDEBUG AFTER reached_end_any FILTER:")
        debug_after = (
            case_df[case_df["order"] == "second_order"]
                .groupby("prefixes")["nodes_mult"]
        )

        print("  min / max / nunique by prefix:")
        print(debug_after.agg(['min', 'max', 'nunique']))

        print("\n  full unique nodes_mult by prefix:")
        print(debug_after.apply(lambda s: sorted(s.unique())))
        print("---------------------------------------")
        # -----------------------------------------


    
    if "tracking_cols_keeping" in Debug: 
        # ---------- DEBUG BLOCK 3 ----------
        print("\nDEBUG nodes_mult PARSING — NaN rows:")
        nan_rows = case_df[case_df["nodes_mult"].isna()]
        print(nan_rows[["prefixes", "order", "source_file"]].head(20))
        print("Total NaN rows:", len(nan_rows))
        print("---------------------------------------")
        # -----------------------------------------

    # Extract nodes_mult...
    case_df = case_df.dropna(subset=["nodes_mult"])
    case_df["nodes_mult"] = case_df["nodes_mult"].astype(int)
    
    # Save a pristine copy BEFORE plotting filters
    case_df_full = case_df.copy()


    # Drop rows without nodes_mult (if any)
    case_df = case_df.dropna(subset=["nodes_mult"])
    case_df["nodes_mult"] = case_df["nodes_mult"].astype(int)
    
    # Sanity check 
    if "infer_order_debug" in Debug:
        print("Unique inferred orders:", case_df["order"].unique())
        print(case_df[["source_file", "order"]]) # .head(20)
   

   
    # Build reference table if comparing SAM vs refined SAM
    if ERROR_MODE in ("self_ref", "self_ref_second_order"):
        ref_map = build_reference_table(case_df_full, mode=ERROR_MODE)
    else:
        ref_map = None


    # --- Compute error metrics for each row ---
    all_rows = []
    for _, row in case_df.iterrows():
        extra = compute_errors_for_row(row, exp_df=exp_df, ref_map=ref_map, mode=ERROR_MODE)
        if extra is None:
            # No experimental mapping for this prefix, just skip it.
            continue
        combined = dict(row)  # original fields (includes 'order')
        combined.update(extra)  # add error metrics
        all_rows.append(combined)

    if not all_rows:
        raise RuntimeError("No rows could be matched to experimental data. Check prefix->column mapping.")

    full_df = pd.DataFrame(all_rows)
    # Force script_runtime to numeric (important!)
    full_df["script_runtime"] = pd.to_numeric(full_df["script_runtime"], errors="coerce")


    if "tracking_cols_keeping" in Debug: 
        # ---------- DEBUG BLOCK 4 ----------
        print("\nDEBUG second-order nodes_mult that reached FULL_DF:")
        debug_full = (
            full_df[full_df["order"] == "second_order"]
                .groupby("prefixes")["nodes_mult"]
        )

        print("  min / max / nunique by prefix:")
        print(debug_full.agg(['min', 'max', 'nunique']))

        print("\n  full unique nodes_mult by prefix:")
        print(debug_full.apply(lambda s: sorted(s.unique())))
        print("---------------------------------------")
        # -----------------------------------------


    # Sort nicely by prefix, order, and nodes_mult
    sort_cols = [c for c in ["prefixes", "order", "nodes_mult"] if c in full_df.columns]
    full_df = full_df.sort_values(sort_cols).reset_index(drop=True)
    # ---- MAKE PLOTS (optional) ----
    if make_plots:
        make_convergence_plots(full_df, out_dir, max_nodes_global=MAX_NODES_GLOBAL, max_nodes_by_prefix=MAX_NODES_BY_PREFIX)
        make_runtime_plots(full_df,out_dir,max_nodes_global=MAX_NODES_GLOBAL,max_nodes_by_prefix=MAX_NODES_BY_PREFIX)
    # --- Output 1: Full analysis CSV ---
    
    full_path = out_dir / "validation_analysis_full.csv"
    full_df_out = filter_columns(full_df)
    full_df_out.to_csv(full_path, index=False)
    print(f"Wrote full analysis to: {full_path}")


    # --- Output 2: Short paper-style table ---
    if write_paper:
        paper_cols = PAPER_COLS
        paper_cols = [c for c in paper_cols if c in full_df.columns]  # safety
        paper_df = full_df[paper_cols].copy()
        paper_df = filter_columns(paper_df, paper=True)
        
        paper_path = out_dir / "validation_analysis_paper_table.csv"
        paper_df.to_csv(paper_path, index=False)
        print(f"Wrote paper table to: {paper_path}")
    # --- Output 3: Summary for another script / paper table ---
    # For ERROR_MODE == "exp":
    #     - keep existing behavior: best (min rmse_K) vs experiment per prefix.
    #
    # For ERROR_MODE in {"self_ref", "self_ref_second_order"}:
    #     - take *only* the refined reference case(s) and compare those to experiment.
    #
    if write_summary:

        # Ensure experimental data is available for summary, regardless of ERROR_MODE
        if exp_df is None:
            exp_df_local = pd.read_csv(args.exp_csv)
            exp_df_local.columns = exp_df_local.columns.str.strip()

            if "Kelvin" not in exp_df_local.columns:
                raise RuntimeError(
                    f"Expected a 'Kelvin' column in {args.exp_csv}, got columns: {list(exp_df_local.columns)}"
                )

            exp_df_local["Kelvin"] = exp_df_local["Kelvin"].astype(str).str.strip()
            exp_df_local = exp_df_local.set_index("Kelvin")
            exp_df_local.index = exp_df_local.index.astype(str).str.strip()
            for col in exp_df_local.columns:
                exp_df_local[col] = pd.to_numeric(exp_df_local[col], errors="coerce")
        else:
            exp_df_local = exp_df

        # ---- Case 1: ERROR_MODE == "exp" (already comparing vs experiment) ----
        if ERROR_MODE == "exp":
            summary_df = (
                full_df.sort_values(["prefixes", "rmse_K"])
                .groupby("prefixes", as_index=False)
                .first()
            )
            summary_cols = [c for c in SUMMARY_COLS if c in summary_df.columns]
            summary_df = summary_df[summary_cols].copy()

        # ---- Case 2: SAM-vs-SAM modes -> summary is refined SAM vs experiment ----
        else:
            summary_rows = []

            if ERROR_MODE == "self_ref_second_order":
                # One reference per prefix: finest second-order row
                df_second = case_df_full[case_df_full["order"] == "second_order"].copy()
                grouped = df_second.groupby("prefixes", dropna=False)

                for prefix, grp in grouped:
                    cap = get_nodes_cap_for_prefix(prefix)
                    if cap is not None:
                        grp = grp[grp["nodes_mult"] <= cap]
                    if grp.empty:
                        # no rows for this prefix under the cap, skip
                        continue

                    idx = grp["nodes_mult"].idxmax()
                    base_row = grp.loc[idx]
                    extra = compute_exp_errors_for_row(base_row, exp_df_local)
                    if extra is None:
                        continue
                    combined = dict(base_row)
                    combined.update(extra)
                    summary_rows.append(combined)


            elif ERROR_MODE == "self_ref":
                # One reference per (prefix, order): finest mesh of that family
                grouped = case_df_full.groupby(["prefixes", "order"])

                for (prefix, order), grp in grouped:
                    cap = get_nodes_cap_for_prefix(prefix)
                    if cap is not None:
                        grp = grp[grp["nodes_mult"] <= cap]
                    if grp.empty:
                        continue

                    idx = grp["nodes_mult"].idxmax()
                    base_row = grp.loc[idx]
                    extra = compute_exp_errors_for_row(base_row, exp_df_local)
                    if extra is None:
                        continue
                    combined = dict(base_row)
                    combined.update(extra)
                    summary_rows.append(combined)


            else:
                raise ValueError(f"Unexpected ERROR_MODE in summary block: {ERROR_MODE}")

            if not summary_rows:
                raise RuntimeError(
                    "No rows could be matched to experimental data for summary. "
                    "Check prefix->column mapping and ERROR_MODE."
                )

            summary_df = pd.DataFrame(summary_rows)

            # Nice, paper-ready columns: refined SAM vs experiment
            summary_cols = [c for c in SUMMARY_COLS if c in summary_df.columns]
            summary_df = summary_df[summary_cols].copy()    

        # Apply column toggles (note: filter_columns is written for ref_*,
        # so it will generally leave exp_* columns alone, which is what we want)
        summary_df = filter_columns(summary_df)

        summary_path = out_dir / "validation_analysis_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"Wrote summary to: {summary_path}")



if __name__ == "__main__":
    main()
