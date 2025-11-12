########## CSV Maker
## First made: 23 Oct 25
## Today editing: 23 Oct 25

# Purpose of this script: Analyze the results of the runs to try and get useful insights. 


##############################################

import glob, os, re
from natsort import natsorted
import pandas as pd

run_identifiers = ["first_order_nm/"] # Suggest you do one at a time, avoid vibe coding
prefixes = ["jsalt1", "jsalt2", "jsalt3", "jsalt4"]
end_times = [700, 850, 100000] # possible end times in your file. 

for prefix in prefixes:
    files = natsorted(glob.glob(f"{prefix}*.csv"))
    print("currently on file: \n",files)
    if not files:
        print(f"[WARN] No files for {prefix}")
        continue

    out_rows = []
    for f in files:
        try:
            # Read whole CSV (robust to headers/quotes), then take last data row
            df = pd.read_csv(f)
            if df.empty: 
                print(f"[SKIP] Empty file: {f}")
                continue
            last = df.tail(1).copy()
            last.insert(0, "source_file", os.path.basename(f))  # put filename as first column
            out_rows.append(last)
        except Exception as e:
            print(f"[ERROR] {f}: {e}")

    if out_rows:
        combined = pd.concat(out_rows, ignore_index=True)
        out_path = f"analysis/combined_last_lines_{prefix}.csv"

        os.makedirs(os.path.dirname(out_path), exist_ok=True) # will make the directory needed if analysis doesn't exist yet
        combined.to_csv(out_path, index=False)
        print(f"[OK] Wrote {len(combined)} rows → {out_path}")
    else:
        print(f"[WARN] No rows collected for {prefix}")

