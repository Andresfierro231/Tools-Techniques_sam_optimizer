from __future__ import annotations
import re

"""
Placeholder for future post-processing.
Responsibilities:

Will parse SAM output logs to extract metrics such as residual norms, nonlinear iteration counts, or divergence indicators.

Later, can compute RMSE versus experimental data.
"""

# Fill these regexes based on your SAM output format.
RE_TIME = re.compile(r"time\s*=\s*([0-9.]+)")
RE_NL_RES = re.compile(r"Nonlinear residual:\s*([0-9.eE+-]+)")
RE_LIN_RES = re.compile(r"Linear solve:\s*residual\s*=\s*([0-9.eE+-]+)")

def parse_time(line: str):
    m = RE_TIME.search(line)
    return float(m.group(1)) if m else None

def parse_nl_res(line: str):
    m = RE_NL_RES.search(line)
    return float(m.group(1)) if m else None

def parse_lin_res(line: str):
    m = RE_LIN_RES.search(line)
    return float(m.group(1)) if m else None
