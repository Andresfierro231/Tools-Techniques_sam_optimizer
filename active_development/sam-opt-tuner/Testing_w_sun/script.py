import subprocess
import pandas as pd
import time, os, tempfile, shutil
# import pyhit
# import moosetree

node_mult_list = [2, 6, 12, 24, 48, 80, 100, 150, 300, 400, 600]

for node_mult in node_mult_list:

    for i in [1,2,3,4]:
        
        #Takes input file template and creates file name to be used, call it file
        inputfile = f"jsalt{i}.i"
        file = f"jsalt{i}_nodes_mult_by_{node_mult}.i"
        
        with open(inputfile, "r") as f_in:
            lines = f_in.readlines() 
            # substitutes lines for node multiplier

            with open(file, "w") as f_out:
                for line in lines:
                    if "node_multiplier" in line:
                        f_out.write(f"node_multiplier := {node_mult}\n")
                    else: 
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

        elapsed = time.time() - start_time

        if proc.returncode ==0: 
            os.remove(tmp_path) # Succesful run, no log kept
        else: 
            final_log = f"{file}.txt"
            with open(tmp_path, "a") as logf:
                logf.write(f"\n# Script runtime: {elapsed:.3f} seconds\n")
            shutil.move(tmp_path, final_log) # keeps the log, has the descriptive name








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
