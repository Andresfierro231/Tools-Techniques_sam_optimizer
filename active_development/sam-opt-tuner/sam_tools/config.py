from __future__ import annotations
import yaml, pathlib
"""
Lightweight utilities for configuration.
Responsibilities:

load_yaml(path) – load experiment configuration files (YAML).

ensure_results_dir(path) – create the results folder tree if missing.
"""

def load_yaml(path):
    p = pathlib.Path(path)
    with p.open("r") as f:
        return yaml.safe_load(f)

def ensure_results_dir(base_dir):
    p = pathlib.Path(base_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p
