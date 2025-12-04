# SAM Optimizer (`sam-opt-tuner`)

This folder contains the early pieces of a SAM optimizer workflow for the
molten-salt loop project. It wraps existing scripts and SAM input files with:

- Centralized runtime logging
- A clean way to launch SAM runs with different hyperparameters
- A simple live monitor to track progress

## File Overview

- `config.py`  
  Central **control panel**. Change hyperparameter ranges, runtime caps,
  and path settings here.

- `runtime_logger.py`  
  Handles timing of SAM runs using `time.perf_counter()` and writes a single
  `runtimes_master.csv` file with one row per run.

- `run_launcher.py`  
  Provides `run_sam_case(...)` which:
  - Builds a concrete `.i` file from a template and hyperparameters,
  - Runs SAM with a timeout,
  - Logs runtime and status via `runtime_logger`.

- `monitor.py`  
  Command-line **live monitor**. Re-reads `runtimes_master.csv` every few seconds
  and prints a summary of runs.

- `__init__.py`  
  Marks this directory as a Python package and exposes `CONFIG` at the top level.

## Quickstart

1. Make sure the paths in `config.py` match your repo layout:

   - `templates_dir` should point to your existing `Templates` directory.
   - `runtime_log` should point to where you want `runtimes_master.csv` to live.

2. In a Python shell or small script, run a test case:

   ```python
   from sam_opt.run_launcher import run_sam_case

   result = run_sam_case(
       case_name="jsalt1",
       template_name="jsalt1.i",
       hyperparams={
           "node_multiplier": 8,
           "order": 2,
           "htc": 1000.0,  # optional for now
       },
   )
   print(result)
   ```

3. Live Monitoring
    - In a second terminal 

    ```bash
    cd active_development
    python -m sam_opt.monitor
    ```
    We should find a summary of logged runs (total, by status, runtime stats)

     