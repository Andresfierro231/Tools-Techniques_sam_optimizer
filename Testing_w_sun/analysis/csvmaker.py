########## CSV Maker
## First made: 23 Oct 25
## Today editing: 23 Oct 25

# Purpose of this script: Analyze the results of the runs to try and get useful insights. 

# [x] Succesfully compiles last line of each prefix in case
# [] Reporting paper
#       [X] For each case, report how many succesful for each prefix, and how many failed. 
#       [] make a cross comparison and how much difference from each other


##############################################

import glob, os, re
from natsort import natsorted, index_natsorted, natsort_keygen
import pandas as pd

from collections import defaultdict
case_records = defaultdict(list)  # case -> list of dict rows (one per prefix file's last row)
TOL = 1e-10

case_identifiers = ["First_order_nm_nureth26", "second_order_nm_exp_nureth26"] # Where files are, name of directory you want to search
prefixes = ["jsalt1", "jsalt2", "jsalt3", "jsalt4"] # Name of type of file you want to parse csv
end_times = [700, 850, 100000] # possible end times in your file. 

def _find_time_col(df):
    #  finding time col
    for col in df.columns:
        colName = str(col).lower()
        if colName == "time":
            return col 

def _nearest_end_time(t, ends, tol): # Returns the nearest end value to one of the end times we expect
    # Returns (matched_bool, matched_value or None)
    for e in ends:
        if abs(float(t) - float(e)) <= tol:
            return True, e
    return False, None
def get_script_runtime(txt_path):
    """Return runtime in seconds if found in text file, else None."""
    try:
        with open(txt_path, "r") as f:
            lines = f.readlines()
        # Find the last line starting with '#'
        for line in reversed(lines):
            if line.strip().startswith("#"):
                match = re.search(r"runtime:\s*([\d.]+)\s*seconds", line, re.IGNORECASE)
                if match:
                    return float(match.group(1))
                break
    except Exception:
        pass
    return None

# Main code
for case in case_identifiers: 
    for prefix in prefixes:
        text_files = natsorted(glob.glob(os.path.expanduser(f"~/projects/physor2026_andrew/Testing_w_sun/{case}/{prefix}*.txt"))) # This is what searches for files
        runtime_by_source = {}        

        for txt in text_files: # Adds data labels 
            runtime = get_script_runtime(txt)

            if runtime is not None:
                runtime_by_source[os.path.basename(txt).replace(".i.txt", "_csv.csv")] = runtime

        files = natsorted(glob.glob(os.path.expanduser(f"~/projects/physor2026_andrew/Testing_w_sun/{case}/{prefix}*.csv"))) # This is what searches for files

        # What am I reading, and did it work? 
        print("currently on file of case :",case, "; run :",prefix, "\n", )
        if not files:
            print(f"[WARN] No files for {prefix} \n")
            continue

            
        ### Collecting outrows and making csv
        out_rows = []
        for file in files:
            try: # Read whole CSV 
                df = pd.read_csv(file, engine="python", on_bad_lines="skip")
                
                ## Taking last row
                if df.empty: 
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
            out_path = f"analysis/{case}_analysis/combined_last_lines_{prefix}.csv" # if no files to be made

            os.makedirs(os.path.dirname(out_path), exist_ok=True) # will make the directory needed if analysis doesn't exist yet
            combined.to_csv(out_path, index=False)
            print(f"[OK] Wrote {len(combined)} rows → {out_path} \n")
        else:
            print(f"[WARN] No rows collected for {prefix} \n")
        
                # ADD (per-case report once all prefixes processed):
        if case_records[case]:
            # Flatten rows into one DataFrame and sort
            case_df = pd.concat(case_records[case], ignore_index=True)
            case_df = case_df.sort_values(["case", "source_file"], ascending=[True, True])

            # Identify plausible temperature columns
            temp_cols = [c for c in case_df.columns
                         if isinstance(c, str) and ("temp" in c.lower() or c.lower().startswith("t_") or c.lower().startswith("tp"))]
            if not temp_cols:
                temp_cols = [c for c in case_df.columns if str(c).lower() in ("temperature", "temp")]

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
            

            # Attach mean of temperature columns per file (if present)
            if temp_cols:
                temp_means = (case_df.groupby(["case", "source_file"])[temp_cols]
                              .mean(numeric_only=True)
                              .reset_index())
                file_report = file_report.merge(temp_means, on=["case", "source_file"], how="left")

            # Simple counts for the summary
            num_reached = int(file_report["reached_end_any"].sum())
            num_total   = len(file_report)
            print(f"[REPORT] {case}: {num_reached}/{num_total} files reached an allowed end_time.\n")

            # Write per-case report
            report_dir = f"analysis/{case}_analysis"
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
                for _, row in successes.iterrows():
                    fh.write(f"  - {row['source_file']} @ {row['matched_end_time']}  (prefixes: {row['prefixes']})\n")

            print(f"[OK] Wrote per-case report → {report_path}\n[OK] Wrote summary → {meta_path}\n")
        else:
            print(f"[WARN] No records captured for case {case}\n")
