########## CSV Maker
## First made: 23 Oct 25
## Today editing: 17 Nov 25

# ⭐️ BEFORE USING: make sure to ⭐️
#       rm ../Templates/*_cp*
#       mv ../Templates/*_nodes_mult_* ./analysis/<case_identifier_of_choice>/

# Purpose of this script: 
#   Makes case reports and summary from full run csv. 
#       (Analyze the results of the runs to try and get useful insights). 

# [x] Succesfully compiles last line of each prefix in case
# [] Reporting paper
#       [X] For each case, report how many succesful for each prefix, and how many failed. 
#       [] make a cross comparison and how much difference from each other
##############################################
#Script does 2 main things
# 1.  For each (case, prefix):
    # Find all matching CSV files.
    # Take only the last row of each CSV (the final time step), tag it with metadata, and write:
    # One combined CSV per prefix: combined_last_lines_<prefix>.csv.
# 2. For each case:
    # Aggregate all those last rows (from all prefixes).
    # Build a per-file report that answers:
    # Did this file reach a valid end time?
    # What was its final time?
    # Which prefixes contributed?
    # What was the average temperature, runtime, etc.?
# 3. Save:
    # analysis/{case}_analysis/case_report.csv (structured table).
    # analysis/{case}_analysis/summary.txt (human-readable summary)
#~
##############################################

import glob, os, re
from natsort import natsorted, index_natsorted, natsort_keygen
import pandas as pd
from pathlib import Path

from collections import defaultdict
case_records = defaultdict(list)  # case -> list of dict rows (one per prefix file's last row)
TOL = 1e-10

case_identifiers = [ "analysis/temp_test"] # "analysis/coarse_second_order_nm_nureth26", "analysis/coarse_first_order_nm_physor_not_nureth26"] #, "Fine_first_order_nm_nureth26_analysis", "Fine_second_order_nm_exp_nureth26_analysis"] #  # Where files are, name of directory you want to search # search uses: os.path.expanduser(f"~/projects/physor2026_andrew/Testing_w_sun/{case}/{prefix}*.txt"))
prefixes = ["jsalt1", "jsalt2", "jsalt3", "jsalt4"] # Name of type of file you want to parse csv
end_times = [700, 850, 100000] # possible end times in your file. 

RUNTIME_CSV = "sam_runtime.csv"
RUNTIME_TXT = "sam_runtimes.txt"

# Search in base directory
THIS_DIR = Path(__file__).resolve().parent
ANALYSIS = THIS_DIR.parents[1]
BASE = THIS_DIR.parents[2]   # or parents[1], depending on where the file lives

def _find_time_col(df):
    #  finding time col. This column used elsewhere
    for col in df.columns:
        colName = str(col).lower()
        if colName == "time":
            return col 

def _nearest_end_time(t, ends, tol): 
    # Returns the nearest end value to one of the end times we expect. Used to decide if run reached final time step/finished
    # Returns (matched_bool, matched_value or None)
    for e in ends:
        if abs(float(t) - float(e)) <= tol:
            return True, e
    return False, None

def load_runtime_map(case_identifiers):
    """
    Look for runtime logs:
        - sam_runtime.csv (global)
        - sam_runtimes.txt (global)
        - {case}/sam_runtime.csv
        - {case}/sam_runtimes.txt

    Return: dict mapping 'jsaltX_nodes_mult_by_Y_csv.csv' -> runtime_seconds
    """
    runtime_by_source = {}



    # ---------- helper to record a row ----------
    def add_entry(file_path, runtime):
        base = os.path.basename(file_path.strip())        # 'jsalt1_nodes_mult_by_1.i'
        csv_name = base.replace(".i", "_csv.csv")         # 'jsalt1_nodes_mult_by_1_csv.csv'
        runtime_by_source[csv_name] = runtime

    # ---------- helper to load CSV ----------
    def load_csv(path):
        print(f"[INFO] Loading runtimes from {path}")
        df = pd.read_csv(path)
        if "runtime_seconds" in df.columns:
            col = "runtime_seconds"
        elif "runtime" in df.columns:
            col = "runtime"
        else:
            print(f"[WARN] {path} has no runtime column")
            return
        for _, row in df.iterrows():
            add_entry(row["file"], float(row[col]))

    # ---------- helper to load TXT ----------
    def load_txt(path):
        print(f"[INFO] Loading runtimes from {path}")
        with open(path, "r") as f:
            for line in f:
                m = re.match(r"([^,]+),\s*returncode=.*?runtime=\s*([\d.]+)", line)
                if m:
                    add_entry(m.group(1), float(m.group(2)))

    # ---------- 1. Check global files ----------
    global_csv = os.path.join(BASE, "sam_runtime.csv")
    global_txt = os.path.join(BASE, "sam_runtimes.txt")

    if os.path.exists(global_csv):
        load_csv(global_csv)
    if os.path.exists(global_txt):
        load_txt(global_txt)

    # ---------- 2. Check per-case runtime files ----------
    for case in case_identifiers:
        case_dir = os.path.join(BASE, case)
        csv_p = os.path.join(case_dir, "sam_runtime.csv")
        txt_p = os.path.join(case_dir, "sam_runtimes.txt")

        if os.path.exists(csv_p):
            load_csv(csv_p)
        if os.path.exists(txt_p):
            load_txt(txt_p)

    print(f"[INFO] Loaded total {len(runtime_by_source)} runtime entries.")
    return runtime_by_source



# Build global map once
runtime_by_source = load_runtime_map(case_identifiers)
# Sanity check
if not runtime_by_source:
    print("[WARN] runtime_by_source is empty – check that your sam_runtime.csv or sam_runtimes.txt is in the working directory.")



# Main code
    # Loops over all cases and prefixes
for case in case_identifiers: 
    for prefix in prefixes:
        search_dir = THIS_DIR / case
        files = natsorted(glob.glob(str(search_dir / f"{prefix}*.csv"))) # This is how to search for files


        # Outputs What  I am reading, and did if it worked
        print("currently on file of case :", case, "; run :", prefix, "\n", )
        if not files:
            print(f"[WARN] No files for {prefix} \n")
            continue
        

            
        ### Collecting outrows and making csv
        out_rows = []
        for file in files:
            try: # Read whole CSV 
                df = pd.read_csv(file, engine="python", on_bad_lines="skip")
                
                ## Taking onlly last row last row
                if df.empty: 
                    # Skipping empty files
                    print(f"[SKIP] Empty file: {file}\n")
                    continue
                last = df.tail(1).copy() # last is the last entry in csv
                last.insert(1, "prefix", prefix)
                last.insert(2, "case", case)
                last_time_val = float(last[_find_time_col(df)].iloc[0]) # returns the time value of the final line in that csv
                reached, matched_end = _nearest_end_time(last_time_val, end_times, TOL)
                last["last_time"] = last_time_val
                last["reached_end"] = reached
                last["matched_end_time"] = matched_end

                last.insert(0, "source_file", os.path.basename(file))  # put filename as first column # Headers made automatically by pandas
                runtime_val = runtime_by_source.get(os.path.basename(file))
                last["script_runtime"] = runtime_val
                
                out_rows.append(last)
                case_records[case].append(last) # capture into case_records for per-case report later

                
                


            except Exception as e: # if unable to read csv
                print(f"[ERROR] {file}: {e}\n")
            
        if out_rows:
            combined = pd.concat(out_rows, ignore_index=True) # Makes a file with all the last rows
            out_path = f"{case}_analysis/combined_last_lines_{prefix}.csv" # if no files to be made

            os.makedirs(os.path.dirname(out_path), exist_ok=True) # will make the directory needed if analysis doesn't exist yet
            combined.to_csv(out_path, index=False)
            print(f"[OK] Wrote {len(combined)} rows → {out_path} \n")
        else:
            print(f"[WARN] No rows collected for {prefix} \n")
        

        ### ADD (per-case report once all prefixes processed):
        if case_records[case]:
            # Flatten rows into one DataFrame and sort
            case_df = pd.concat(case_records[case], ignore_index=True)
            case_df = case_df.sort_values(["case", "source_file"], ascending=[True, True])

            

            if "script_runtime" not in case_df.columns:
                case_df["script_runtime"] = pd.NA

            # Build a per-(case, source_file) report:
            # - reached_end_any: whether ANY run for that file reached an allowed end time
            # - last_time: max last_time seen for that file
            # - matched_end_time: most common non-null matched end time for that file
            # - prefixes: which prefixes contributed rows for that file
            file_group = case_df.groupby(["case", "source_file"], as_index=False)

            def _mode_non_null(s):
                s = s.dropna()
                return s.mode().iloc[0] if not s.empty else pd.NA

            file_report = (
                            file_group.agg(
                            reached_end_any=("reached_end", "any"),
                            last_time=("last_time", "max"),
                            matched_end_time=("matched_end_time", _mode_non_null),
                            prefixes=("prefix", lambda s: ",".join(sorted(set(s)))),
                            script_runtime=("script_runtime", "mean"),  # safe now
                        ))
            keygen = natsort_keygen()

            file_report["source_file"] = file_report["source_file"].astype(str)
            file_report["source_file"] = file_report["source_file"].astype(str)
            file_report = file_report.sort_values(
                                                    ["case", "source_file"],
                                                    key=lambda col: col.map(keygen) if col.name == "source_file" else col
                                                ).reset_index(drop=True)
            
            ### TH_Output_cols for analysis case_report.csv ### 
            # Identify useful TH output columns
            cols = [c for c in case_df.columns if isinstance(c, str)]
            def detect_cols(cols, contains=(), startswith=(), exact=(),
                            exclude_contains=(), exclude_startswith=(), exclude_exact=()):
                """Return list of columns whose names match include-rules 
                but do NOT match exclude-rules."""
                
                out = []
                for c in cols:
                    if not isinstance(c, str):
                        continue
                    
                    name = c.lower()

                    # ---------- Exclusion rules ----------
                    if any(bad in name for bad in exclude_contains):
                        continue
                    if any(name.startswith(bad) for bad in exclude_startswith):
                        continue
                    if any(name == bad for bad in exclude_exact):
                        continue

                    # ---------- Inclusion rules ----------
                    if (
                        any(sub in name for sub in contains) or
                        any(name.startswith(pref) for pref in startswith) or
                        any(name == ex for ex in exact)
                    ):
                        out.append(c)
                return out
            TH_Output_cols = detect_cols(
                cols,
                contains=("temp","vel"),
                startswith=("t_", "tp"),
                exact=("massflowrate", "temp"),
                exclude_contains=("template", "attempt", ":"),  # blocks template_id, attempt_count
                exclude_startswith=("t_probe",),           # blocks t_probe_*
                exclude_exact=("temp_flag",),             # blocks exactly "temp_flag"
            )
                        
            
            # Attach mean of temperature columns per file (if present)
            if TH_Output_cols:
                temp_means = (case_df.groupby(["case", "source_file"])[TH_Output_cols]
                              .mean(numeric_only=True)
                              .reset_index())
                file_report = file_report.merge(temp_means, on=["case", "source_file"], how="left")
       

            # Simple counts for the summary
            num_reached = int(file_report["reached_end_any"].sum())
            num_total   = len(file_report)
            print(f"[REPORT] {case}: {num_reached}/{num_total} files reached an allowed end_time.\n")

            # Write per-case report      
            report_dir = f"{case}_analysis"
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, "case_report.csv")
            meta_path   = os.path.join(report_dir, "summary.txt")

            file_report.to_csv(report_path, index=False)

            with open(meta_path, "w") as fh:
                fh.write(f"Case: {case}\n")
                fh.write(f"Files reaching allowed end_time: {num_reached}/{num_total}\n")
                fh.write("Successful files by matched_end_time:\n")

                avg_runtime = file_report["script_runtime"].mean(skipna=True)
                fh.write(f"\nAverage script runtime (s): {avg_runtime:.2f}\n")

                successes = file_report[file_report["reached_end_any"]].copy()
                successes = (
                            successes.sort_values("matched_end_time")
                            .groupby("matched_end_time", group_keys=False)
                            .apply(
                                lambda g: g.iloc[index_natsorted(g["source_file"].astype(str))]  # natural sort within group
                                        .assign(matched_end_time=g.name),                     # <-- put it back
                                include_groups=False
                            )
                            .reset_index(drop=True)
                )
                for _, row in successes.iterrows(): # Printing output foe summary.txt
                    runtime = row.get("script_runtime", None)
                    if pd.isna(runtime):
                        runtime_str = "runtime: N/A"
                    else:
                        runtime_str = f"runtime: {runtime:.2f} s"

                    fh.write(
                        f"  - {row['source_file']} @ {row['matched_end_time']} "
                        f"(prefixes: {row['prefixes']})  \t\t{runtime_str}\n"
                    )


            print(f"[OK] Wrote per-case report → {report_path}\n[OK] Wrote summary → {meta_path}\n")
        else:
            print(f"[WARN] No records captured for case {case}\n")
