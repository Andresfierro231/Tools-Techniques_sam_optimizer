import subprocess # Lets you run bash commands 
import pandas as pd
import pyhit # Helpful to directly interact with input file. Supported by Moose, so cleaner
import moosetree

for i in range(100):
    # run SAM
    result = subprocess.run(['sam-opt', '-i', 'f'input_{i}.i', '>', 'f'log_{i}.']) # This command will wait until 

    # Save SAM output to text file 

    # Read CSV ouput
    df = pd.read_csv('input_{i}_out_csv.csv')


    # Analyze output and determine what to change
    x, y = 3,7


    # Load input files and change some params
    # # pyhit changes input file 
    root = pyhit.load('input.i')
    pipe = moosetree.find(root, func=lambda n: n.fullpath =='/Components/<pipe_3>') # for example
    pipe['User_defined_HTC_parameters'] = f"'{x} {y} 0 0 0 0 0'

    # Write input file
    pyhit.write(f'input_{i}.i, root')
