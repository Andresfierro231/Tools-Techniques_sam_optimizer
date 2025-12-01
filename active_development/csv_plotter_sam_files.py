# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# 
#           CSV Plotter
# 
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#  Generates time-series plots from a CSV file.
# Supports individual, grouped, and custom overlay plots (with keyword matching),
# optional zoom, scatter/line toggles, and flexible column filtering.
# Please find more documentation in the bottom of the file.

# #%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%
# Quick start: Put keywords on plot_only_these_cols. 
# More advanced, create a group_keywords. Make sure Plot = True
# #%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%#%

import os
import shutil
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')

# === SETTINGS ===
filepath =  'twosalt1_csv.csv' # 'twowater3_csv.csv' # #   # sam/share/sam/active_development/twoPhase_water/
time_in_hours = False

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Plot = True                 # Whether to plot or not%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
scatter_not_plot = True  # True for scatter, False for line plots
size = 1  # marker size or line width

## Zoom ## 
enable_zoom = True
separate_files = True         # Not sure what this does # ~~Only~plot non-zoomed version once if True~~
separate_zoom_folders = False  # Set to False to save everything in one folder
# Bounds
zoom_lower_bound_list = [0, 30] # [0]
zoom_upper_bound = 0  # zero means no upper bound

debug = False
pdf = False  # save as PDF vs PNG
png_quality = 150  # DPI for PNG: 72(screen),150(default),300(high)


# === Preliminary Cleanup ===
basename = os.path.splitext(os.path.basename(filepath))[0]
main_output_dir = f"{basename}_plots"
title_prefix = basename.split('_')[0]
if os.path.exists(main_output_dir): shutil.rmtree(main_output_dir)
os.makedirs(main_output_dir, exist_ok=True)

# Track what we've plotted if separate_files is enabled
plotted_full_range = set()

for zoom_lower_bound in zoom_lower_bound_list:
    if Plot: 
        current_output_dir = (os.path.join(main_output_dir, f"zoom_{zoom_lower_bound}") if separate_zoom_folders else main_output_dir)
        os.makedirs(current_output_dir, exist_ok=True)
        # === CUSTOM OVERLAY DEFINITIONS ===
        def match_any(substrings, exclude_substrings=None):
            """Match columns containing ANY of `substrings` but NONE of `exclude_substrings`."""
            exclude_substrings = exclude_substrings or []
            def single_match(col):
                col_lower = col.lower()
                return (
                    any(sub.lower() in col_lower for sub in substrings)
                    and not any(exc.lower() in col_lower for exc in exclude_substrings)
                )
            return lambda cols: [col for col in cols if single_match(col)]


        def match_all(substrings, exclude_substrings=None):
            """Match columns containing ALL of `substrings` but NONE of `exclude_substrings`."""
            exclude_substrings = exclude_substrings or []
            def single_match(col):
                col_lower = col.lower()
                return (
                    all(sub.lower() in col_lower for sub in substrings)
                    and not any(exc.lower() in col_lower for exc in exclude_substrings)
                )
            return lambda cols: [col for col in cols if single_match(col)]


        def match_and_any(required, optional, exclude_substrings=None):
            """Match columns with ALL `required` and ANY `optional`, but NONE of `exclude_substrings`."""
            exclude_substrings = exclude_substrings or []
            def single_match(col):
                col_lower = col.lower()
                return (
                    all(r.lower() in col_lower for r in required)
                    and any(o.lower() in col_lower for o in optional)
                    and not any(exc.lower() in col_lower for exc in exclude_substrings)
                )
            return lambda cols: [col for col in cols if single_match(col)]


        def match_split(lhs_keys, rhs_keys, exclude_substrings=None):
            """Split into two lists (lhs, rhs) based on `lhs_keys` and `rhs_keys`, excluding any with `exclude_substrings`."""
            exclude_substrings = exclude_substrings or []
            def matcher(all_columns):
                lhs = [col for col in all_columns
                    if any(k.lower() in col.lower() for k in lhs_keys)
                    and not any(exc.lower() in col.lower() for exc in exclude_substrings)]
                rhs = [col for col in all_columns
                    if any(k.lower() in col.lower() for k in rhs_keys)
                    and not any(exc.lower() in col.lower() for exc in exclude_substrings)]
                return lhs, rhs
            return matcher
        ####

        # === FILTER COLUMNS TO PLOT INDIVIDUALLY ===
        # Leave empty to plot all; otherwise only columns that contain ANY of these keywords will be plotted
        # Plots individual plots
        plot_only_these_cols = ['01', '03', 'courant']# ['dt', 'TP', 'void', 'd']  # e.g., ['TP_', 'void', 'rho']

        # === GROUP DEFINITIONS (Keyword-based matchers) ===
        group_keywords = {
            "TP": lambda col: col.startswith("TP"),
            "rho": lambda col: "rho" in col.lower(),
            "vel": lambda col: "vel" in col.lower(),
            "gas and void": lambda col: "gas" in col.lower() or "void" in col.lower(),
        }
        group_conditions = {key: [] for key in group_keywords}

        # === Overlain PLOTTING ===
        # Define your custom overlays here (with optional excludes)
        custom_overlays = {
            # "dt and Gas Content": match_any(['dt', 'void', 'gas']),
            "Temps": match_any(['temp']),
            # "Left Gas Content": match_and_any(['left'], ['void', 'gas']), # Col with first [] and any of the second []
            "DT vs Gas Content": match_split(['void', 'gas'], ['dt'], exclude_substrings=['area', 'vel']),
        }

        # === COLUMN CLASSIFICATION ===
        def classify_column(col, group_dict):
            """Assigns `col` into one of the groups in `group_dict` based on its name."""
            for key, condition in group_keywords.items():
                if condition(col):
                    group_dict[key].append(col)

        # === PLOTTING FUNCTIONS ===
        def plot_columns(time, df, cols, filename, title, ylabel, current_output_dir,
                        zoom_mask=None, scatter=True, size=1, legend=True, plot_full_range=True):
            valid_cols = [c for c in cols if c in df.columns]
            if debug and valid_cols != cols:
                missing = set(cols) - set(valid_cols)
                for m in missing:
                    print(f"Warning: '{m}' not in DataFrame, skipping in '{title}'")
            if not valid_cols:
                return

            # Only plot full-range if allowed (avoid duplicates across zooms)
            if plot_full_range:
                # If separate_files is on, only plot once per file base name
                key = (filename, 'full')
                if not separate_files or key not in plotted_full_range:
                    plt.figure()
                    for c in valid_cols:
                        if scatter:
                            plt.scatter(time, df[c], label=c, s=size)
                        else:
                            plt.plot(time, df[c], label=c)
                    plt.xlabel("Time [hr]" if time_in_hours else "Time [s]")
                    plt.ylabel(ylabel)
                    # Title
                    full_title = f"{title_prefix}\n{title}"
                    plt.title(full_title)
                    if legend and len(valid_cols) > 1:
                        plt.legend()
                    plt.grid(True)
                    ext = 'pdf' if pdf else 'png'
                    full_path = os.path.join(main_output_dir, f"{filename}_vs_time.{ext}")
                    plt.savefig(full_path, dpi=None if pdf else png_quality, bbox_inches='tight')
                    plt.close()
                    if separate_files:
                        plotted_full_range.add(key)
            # Zoomed plot (always save to per-zoom dir)
            if enable_zoom and zoom_mask is not None and zoom_mask.any():
                plt.figure()
                for c in valid_cols:
                    if scatter:
                        plt.scatter(time[zoom_mask], df[c][zoom_mask], label=c, s=size)
                    else:
                        plt.plot(time[zoom_mask], df[c][zoom_mask], label=c)
                plt.xlabel("Time [hr]" if time_in_hours else "Time [s]")
                plt.ylabel(ylabel)
                # Title
                full_title = f"{title_prefix}\n{title}"
                plt.title(f"{full_title} (Zoomed > {zoom_lower_bound}{' hr' if time_in_hours else ' s'})")
                if legend and len(valid_cols) > 1:
                    plt.legend()
                plt.grid(True)
                ext = 'pdf' if pdf else 'png'
                zoom_path = os.path.join(current_output_dir, f"{filename}_vs_time_zoom_LB={zoom_lower_bound}.{ext}")
                plt.savefig(zoom_path, dpi=None if pdf else png_quality, bbox_inches='tight')
                plt.close()

        def plot_columns_dual_y(time, df, lhs_cols, rhs_cols, filename, title, current_output_dir,
                                zoom_mask=None, scatter=True, size=1):
            # Only plot full-range if allowed
            key = (filename, 'dual_full')
            if not separate_files or key not in plotted_full_range:
                fig, ax1 = plt.subplots()
                ax2 = ax1.twinx()
                for c in lhs_cols:
                    if scatter:
                        ax1.scatter(time, df[c], label=c, s=size)
                    else:
                        ax1.plot(time, df[c], label=c)
                for c in rhs_cols:
                    if scatter:
                        ax2.scatter(time, df[c], label=c, s=size)
                    else:
                        ax2.plot(time, df[c], label=c)
                ax1.set_xlabel("Time [hr]" if time_in_hours else "Time [s]")
                ax1.set_ylabel("Gas Content / Void")
                ax2.set_ylabel("DT")
                h1, l1 = ax1.get_legend_handles_labels()
                h2, l2 = ax2.get_legend_handles_labels()
                if len(h1 + h2) > 1:
                    ax1.legend(h1 + h2, l1 + l2, loc='upper left', bbox_to_anchor=(1.05, 1))
                ax1.grid(True)
                # Title
                full_title = f"{title_prefix}\n{title}"
                plt.title(full_title)                
                fig.tight_layout()
                ext = 'pdf' if pdf else 'png'
                full_path = os.path.join(main_output_dir, f"{filename}_vs_time.{ext}")
                plt.savefig(full_path, dpi=None if pdf else png_quality, bbox_inches='tight')
                plt.close()
                if separate_files:
                    plotted_full_range.add(key)
            # Zoomed dual-axis plot (always save to per-zoom dir)
            if enable_zoom and zoom_mask is not None and zoom_mask.any():
                fig, ax1 = plt.subplots()
                ax2 = ax1.twinx()
                for c in lhs_cols:
                    if scatter:
                        ax1.scatter(time[zoom_mask], df[c][zoom_mask], label=c, s=size)
                    else:
                        ax1.plot(time[zoom_mask], df[c][zoom_mask], label=c)
                for c in rhs_cols:
                    if scatter:
                        ax2.scatter(time[zoom_mask], df[c][zoom_mask], label=c, s=size)
                    else:
                        ax2.plot(time[zoom_mask], df[c][zoom_mask], label=c)
                ax1.set_xlabel("Time [hr]" if time_in_hours else "Time [s]")
                ax1.set_ylabel("Gas Content / Void")
                ax2.set_ylabel("DT")
                h1, l1 = ax1.get_legend_handles_labels()
                h2, l2 = ax2.get_legend_handles_labels()
                if len(h1 + h2) > 1:
                    ax1.legend(h1 + h2, l1 + l2, loc='upper left', bbox_to_anchor=(1.05, 1))
                ax1.grid(True)
                # Title
                full_title = f"{title_prefix}\n{title}"
                plt.title(f"{full_title} (Zoomed)")
                fig.tight_layout()
                ext = 'pdf' if pdf else 'png'
                zoom_path = os.path.join(current_output_dir, f"{filename}_vs_time_zoom_LB={zoom_lower_bound}.{ext}")
                plt.savefig(zoom_path, dpi=None if pdf else png_quality, bbox_inches='tight')
                plt.close()

        df = pd.read_csv(filepath)
        if debug:
            print("Columns in CSV:", df.columns)
            assert os.path.exists(filepath), "File not found!"
            assert "time" in df.columns, "'time' column not found."

        time = df["time"] / 3600 if time_in_hours else df["time"]
        zoom_mask = (time > zoom_lower_bound)
        if zoom_upper_bound > 0:
            zoom_mask &= (time < zoom_upper_bound)

        for col in df.columns:
            if col != "time":
                classify_column(col, group_conditions)

        for col in df.columns:
            if col == "time":
                continue
            if plot_only_these_cols and not any(k.lower() in col.lower() for k in plot_only_these_cols):
                continue
            safe = col.replace(":", "_").replace("-", "_").replace(" ", "_")
            # Only plot full range once if separate_files
            plot_columns(
                time, df, [col], safe, f"{col} vs Time", col,
                current_output_dir, zoom_mask, scatter_not_plot, size, legend=False,
                plot_full_range=(not separate_files or (safe, 'full') not in plotted_full_range)
            )

        for label, cols in group_conditions.items():
            plot_columns(
                time, df, cols, f"All_{label}_group",
                f"{label.upper()} Columns vs Time",
                f"{label.upper()} Variables",
                current_output_dir, zoom_mask, scatter_not_plot, size, True,
                plot_full_range=(not separate_files or (f"All_{label}_group", 'full') not in plotted_full_range)
            )

        for name, matcher in custom_overlays.items():
            res = matcher([c for c in df.columns if c != "time"])
            if isinstance(res, tuple):
                lhs, rhs = res
                if debug:
                    print(f"[DEBUG] {name}: LHS={lhs}, RHS={rhs}")
                plot_columns_dual_y(
                    time, df, lhs, rhs,
                    f"{name}_overlay", f"{name} vs Time",
                    current_output_dir, zoom_mask, scatter_not_plot, size
                )
            else:
                if debug:
                    print(f"[DEBUG] {name}: COLS={res}")
                plot_columns(
                    time, df, res, f"{name}_overlay",
                    f"{name} vs Time", f"{name} Group",
                    current_output_dir, zoom_mask, scatter_not_plot, size, True,
                    plot_full_range=(not separate_files or (f"{name}_overlay", 'full') not in plotted_full_range)
                )

    """
    ============================================================
    CSV Time Series Plotter – Modular, Grouped, and Filtered
    ============================================================
This script loads a time series CSV file (e.g., from a simulation or experiment)
and generates plots for each variable over time, with support for:

    ✅ Individual plots (column vs. time)
    ✅ Grouped plots (by keyword, e.g., all "TP" or "rho" variables)
    ✅ Custom overlays (columns matching logical keyword combinations)
    ✅ Zoomed-in views (based on user-specified time window)
    ✅ Line or scatter plot style
    ✅ Flexible filtering for plotting only specific variables

------------------------------------------------------------
Key Sections and What They Do
------------------------------------------------------------

1. === SETTINGS ===
   Controls file input, zoom range, plotting style, and filtering.

   - `filepath`: path to the CSV file to plot.
   - `time_in_hours`: toggle to convert time to hours.
   - `scatter_not_plot`: scatter vs. line plots.
   - `zoom_lower_bound`, `zoom_upper_bound`: control zoom window.
   - `plot_only_these_cols`: if non-empty, only plot columns containing any of the listed substrings (individual plots only).

2. === GROUP DEFINITIONS ===
   Defines sets of columns (e.g., all "TP" or "rho" variables) to plot together.
   Each group is created using a lambda matcher on column names.

3. === CUSTOM OVERLAYS ===
   Lets you define named plots that combine multiple columns based on flexible keyword matching.

   Uses helper functions:
     • match_any([...]) – matches columns that contain **any** of the given substrings.
     • match_all([...]) – matches columns that contain **all** of the given substrings.
     • (Optional) match_and_any(req, opt) – matches columns with **all required** substrings and **any optional** substring.

   Example:
       "DT Gas": match_all(["dt", "void"]) → columns that include both "dt" and "void".

4. === plot_columns(...) ===
   A reusable function to plot:
     • full time range
     • zoomed-in range
     • legend (if multiple columns)
     • scatter or line style
     • automatic grid, labels, file saving

5. === MAIN WORKFLOW ===
   - Loads CSV and applies time conversion.
   - Classifies columns into defined groups.
   - Filters and plots individual columns based on plot_only_these_cols.
   - Plots all grouped and custom overlay figures (unfiltered).
   - Saves output images to a subdirectory named after the CSV file.

------------------------------------------------------------
How to Use This in the Future
------------------------------------------------------------

• To plot everything:
    plot_only_these_cols = []

• To only plot time series for selected keywords (individually):
    plot_only_these_cols = ['TP', 'dt', 'void']

• To define a custom overlay:
    custom_overlays = {
        "Pressure Points": match_any(["press", "TP"]),
        "Core Metrics": match_all(["core", "temp"]),
    }

• To change from scatter to line plot:
    scatter_not_plot = False

• To zoom in to a time window:
    set zoom_lower_bound and zoom_upper_bound accordingly

    """
