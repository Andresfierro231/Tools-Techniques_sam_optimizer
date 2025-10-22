from __future__ import annotations
import json, hashlib

"""
Small helpers for parameter management.
Responsibilities:

Compute stable hashes of parameter dictionaries (used to name run folders).

Could later include functions to generate randomized or grid search parameters.
"""

def stable_hash(d: dict) -> str:
    blob = json.dumps(d, sort_keys=True, separators=(",",":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]
