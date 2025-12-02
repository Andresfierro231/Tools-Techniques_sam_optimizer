"""
sam_tuner package

Optimizer utilities for SAM molten-salt loop project.

Main modules:
- config: central control panel (hyperparams, runtime limits, paths)
- runtime_logger: centralized runtime logging (runtimes_master.csv)
- run_launcher: utilities to run a single SAM case with hyperparams
- monitor: command-line live monitor for progress

More advanced components (data_handler, models, optimizer_loop, rules)
can be added later without changing the basic structure.
"""

# Expose CONFIG at package level for convenience
from .config import CONFIG  # noqa: F401
