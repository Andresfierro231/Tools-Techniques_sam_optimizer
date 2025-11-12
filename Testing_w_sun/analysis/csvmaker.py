########## CSV Maker
## First made: 23 Oct 25
## Today editing: 23 Oct 25

# Purpose of this script: Analyze the results of the runs to try and get useful insights. 


##############################################

import glob, os, re
from natsort import natsorted
import pandas as pd

case_identifiers = ["First_order_nm_nureth26", "second_order_nm_exp_nureth26"] # Where files are, name of directory you want to search
prefixes = ["jsalt1", "jsalt2", "jsalt3", "jsalt4"] # Name of type of file you want to parse csv
end_times = [700, 850, 100000] # possible end times in your file. 


# Main code
for case in case_identifiers: 
    for prefix in prefixes:
        files = natsorted(glob.glob(os.path.expanduser(f"~/projects/physor2026_andrew/Testing_w_sun/{case}/{prefix}*.csv"))) # This is what searches for files
        
        # What am I reading, and did it work? 
        print("currently on file of case :",case, "; run :",prefix, "\n", )
        if not files:
            print(f"[WARN] No files for {prefix} \n")
            continue
            
        ### Collecting outrows and making csv
        out_rows = []
        for f in files:
            try:
                # Read whole CSV (robust to headers/quotes), then take last data row
                df = pd.read_csv(f)
                if df.empty: 
                    print(f"[SKIP] Empty file: {f}\n")
                    continue
                last = df.tail(1).copy()
                last.insert(0, "source_file", os.path.basename(f))  # put filename as first column
                out_rows.append(last)
            except Exception as e:
                print(f"[ERROR] {f}: {e}\n")

        if out_rows:
            combined = pd.concat(out_rows, ignore_index=True) # Makes a file with all the last rows
            out_path = f"analysis/{case}_analysis/combined_last_lines_{prefix}.csv" # if no files to be made

            os.makedirs(os.path.dirname(out_path), exist_ok=True) # will make the directory needed if analysis doesn't exist yet
            combined.to_csv(out_path, index=False)
            print(f"[OK] Wrote {len(combined)} rows → {out_path} \n")
        else:
            print(f"[WARN] No rows collected for {prefix} \n")

