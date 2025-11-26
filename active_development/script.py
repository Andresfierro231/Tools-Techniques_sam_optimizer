#########################
#  Super short script, just runs and records runtimes in a file called sam_runtimes.txt

#  [] Make sam_runtimes and all of the output be put in a folder with an identifier name, not just dumped in templates
#########################

import subprocess
from pathlib import Path
import pandas as pd
import time, os, tempfile, shutil, csv
# import pyhit
# import moosetree


### -------------------- Small Control Panel -------------------- ###
node_mult_list = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
ORDER = "FIRST" # SECOND
csv_path = Path("Templates/sam_runtimes.csv") # output_dir / "sam_runtimes.csv"

### ------------------------------------------------------------  ###

if ORDER == "FIRST":
    ordr = 1
else: 
    ordr = 2


for node_mult in node_mult_list:

    for i in [1,2,3,4]:
        
        #Takes input file template and creates file name to be used, call it file
        
        inputfile = f"Templates/jsalt{i}.i"
        file = f"Templates/jsalt{i}_nodes_mult_by_{node_mult}.i"
        
        with open(inputfile, "r") as f_in:
            lines = f_in.readlines() 
            # substitutes lines for node multiplier

        replacements = {
            "node_multiplier": f"node_multiplier := {node_mult}\n",
            "quad_order":     f"quad_order := {ORDER}\n",
            "p_order_quadPnts": f"p_order_quadPnts := {ordr}\n"
        }

        with open(file, "w") as f_out:
            for line in lines:
                for key, replacement in replacements.items():
                    if key in line:
                        line = replacement
                        break
                f_out.write(line)



        # Run SAM
        start_time = time.time()


        with tempfile.NamedTemporaryFile(delete=False, suffix =".log") as tmp:
            tmp_path = tmp.name
            # Streams both std_out + std_err into temp file
            with open(tmp_path, "w") as logf:
                proc = subprocess.Popen(f'sam-opt -i {file}', stdout = logf, stderr=logf, text=True, shell=True)
                proc.wait() # waits for command to finish, as Popen lets you do things asynchronously and in parallel
        # result = subprocess.run(f'sam-opt -i {file} 2>&1 | tee {file}.txt', shell=True, check=True)


        # Need to fix output file path so it is automatic
        # output_dir = Path("../analysis")      # your folder name        
        # output_dir.mkdir(parents=True, exist_ok=True)  # makes folder if it doesn't exist
        # summary_path = output_dir / "sam_runtimes.txt"
        # with open(summary_path, "a") as summary:
        #     summary.write(f"{file}, returncode={proc.returncode}, runtime={elapsed:.3f} seconds\n")


        ####################################################
        # Always record runtime in a summary file
                # output_dir = Path("analysis_outputs")
                # output_dir.mkdir(parents=True, exist_ok=True)

        

        elapsed = time.time() - start_time

        # Write header only if file does not exist
        write_header = not csv_path.exists()

        with open(csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow(["file", "returncode", "runtime_seconds"])
            
            writer.writerow([file, proc.returncode, f"{elapsed:.3f}"])
        ####################################################
        # Only keep detailed log if it failed
        if proc.returncode == 0:
            os.remove(tmp_path)
        else:
            final_log = f"{file}.txt"
            with open(tmp_path, "a") as logf:
                logf.write(f"\n# Script runtime: {elapsed:.3f} seconds\n")
                logf.write("# Run FAILED\n")
            shutil.move(tmp_path, final_log)









# Save SAM output to text file

    
# Read CSV output
# df = pd.read_csv(f'input_{i}_out.csv')

# Analyze output and determine what to change
## Blank for now... will analyze later... right now just want to automate some runs

# Load input file and change some params

    ### This form does not work:
    # root = pyhit.load(f'input_{i}.i')
    # pipe = moosetree.find(root, func=lambda n: n.fullpath == '/ComponentInputParameters/pipe_input')
    # pipe['User_defined_HTC_parameters'] = f"'{x} {y} 0 0 0 0 0'"
# Write input file
    # pyhit.write(f'input_{i+1}.i', root)
