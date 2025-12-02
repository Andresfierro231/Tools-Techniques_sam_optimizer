"""
pipeline.py

High-level orchestrator for the SAM optimization workflow.

Stages:
  1. "runs"      : launch SAM sweeps (via top-level script.py).
  2. "analysis"  : run csv_maker.py and csv_analysis.py inside the analysis folder.
  3. "optimizer" : run the surrogate-based optimizer to suggest (and optionally run) hyperparams.

Usage (from active_development):

    # Only run SAM sweeps:
    python -m sam_tuner.pipeline --until runs

    # Run sweeps + csv_maker + csv_analysis:
    python -m sam_tuner.pipeline --until analysis

    # Full pipeline: sweeps + analysis + optimizer (suggest-only):
    python -m sam_tuner.pipeline --until optimizer

    # Full pipeline, with suggest_and_run for jsalt1/jsalt2:
    python -m sam_tuner.pipeline --until optimizer \
        --optimizer-mode suggest_and_run \
        --optimizer-top-k 10 \
        --optimizer-n-run 3 \
        --optimizer-cases jsalt1 jsalt2
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Literal, List, Optional

from .config import CONFIG
from .optimizer_loop import run_optimizer_v0, suggest_and_run_mode


Stage = Literal["runs", "analysis", "optimizer"]


def _project_root() -> Path:
    """
    Return the project root directory that contains script.py and the
    active_development/analysis folder. This assumes this file is inside
    active_development/sam_tuner.
    """
    # This file: .../active_development/sam_tuner/pipeline.py
    here = Path(__file__).resolve()
    # Up two levels: .../active_development
    active_dev = here.parent.parent
    return active_dev


def _analysis_dir() -> Path:
    """
    Return the analysis directory (where csv_maker.py and csv_analysis.py live).
    """
    root = _project_root()
    # CONFIG["paths"]["results_root"] is typically "active_development/analysis"
    # but we'll just trust that for now and resolve it.
    results_root = Path(CONFIG["paths"]["results_root"])
    if not results_root.is_absolute():
        results_root = root / results_root
    return results_root


def run_stage_runs() -> None:
    """
    Stage 1: Run SAM sweeps via top-level script.py.

    This just calls:
        python script.py

    from inside active_development.
    """
    root = _project_root()
    script_path = root / "script.py"

    if not script_path.exists():
        raise FileNotFoundError(
            f"Could not find script.py at: {script_path}\n"
            "Make sure you are in the expected repo layout."
        )

    print("=== PIPELINE: Stage 1 — Running SAM sweeps via script.py ===")
    print(f"[pipeline] Working directory: {root}")
    print(f"[pipeline] Executing: python {script_path.name}")

    subprocess.run(
        ["python", script_path.name],
        cwd=root,
        check=True,
    )

    print("=== PIPELINE: Stage 1 complete ===\n")


def run_stage_analysis() -> None:
    """
    Stage 2: Run csv_maker.py and csv_analysis.py inside the analysis folder.

    Equivalent to:

        cd active_development/analysis
        python csv_maker.py
        python csv_analysis.py
    """
    analysis_dir = _analysis_dir()

    csv_maker = analysis_dir / "csv_maker.py"
    csv_analysis = analysis_dir / "csv_analysis.py"

    if not csv_maker.exists():
        raise FileNotFoundError(f"csv_maker.py not found in {analysis_dir}")
    if not csv_analysis.exists():
        raise FileNotFoundError(f"csv_analysis.py not found in {analysis_dir}")

    print("=== PIPELINE: Stage 2 — Running csv_maker.py ===")
    print(f"[pipeline] Working directory: {analysis_dir}")
    subprocess.run(
        ["python", csv_maker.name],
        cwd=analysis_dir,
        check=True,
    )

    print("=== PIPELINE: Stage 2 — Running csv_analysis.py ===")
    subprocess.run(
        ["python", csv_analysis.name],
        cwd=analysis_dir,
        check=True,
    )

    print("=== PIPELINE: Stage 2 complete ===\n")


def run_stage_optimizer(
    mode: str = "suggest",
    top_k: int = 10,
    n_run: int = 3,
    cases: Optional[List[str]] = None,
) -> None:
    """
    Stage 3: Run the surrogate-based optimizer.

    Parameters
    ----------
    mode : {"suggest", "suggest_and_run"}
        - "suggest"         : train surrogates and print ranked candidates.
        - "suggest_and_run" : do the above, then run the top N candidates.
    top_k : int
        Number of candidates to pass to the optimizer (also printed).
    n_run : int
        Number of candidates to actually run in suggest_and_run mode.
    cases : list of str or None
        Case names to run (e.g. ["jsalt1", "jsalt2"]). If None, defaults inside
        suggest_and_run_mode() to ["jsalt1"].
    """
    print("=== PIPELINE: Stage 3 — Running surrogate-based optimizer ===")
    print(f"[pipeline] Optimizer mode: {mode!r}")

    if mode == "suggest":
        run_optimizer_v0(top_k=top_k, return_df=False)
    else:
        suggest_and_run_mode(
            top_k_suggest=top_k,
            n_run=n_run,
            cases=cases,
        )

    print("=== PIPELINE: Stage 3 complete ===\n")


def run_pipeline(
    until: Stage = "optimizer",
    optimizer_mode: str = "suggest",
    optimizer_top_k: int = 10,
    optimizer_n_run: int = 3,
    optimizer_cases: Optional[List[str]] = None,
) -> None:
    """
    Run the pipeline up to a given stage.

    Parameters
    ----------
    until : {"runs", "analysis", "optimizer"}
        The last stage to execute.
        - "runs"      : only run script.py (SAM sweeps)
        - "analysis"  : runs + csv_maker + csv_analysis
        - "optimizer" : runs + analysis + optimizer (full pipeline)
    optimizer_mode : {"suggest", "suggest_and_run"}
        Mode to pass to Stage 3 optimizer.
    optimizer_top_k : int
        Number of candidates to consider in the optimizer.
    optimizer_n_run : int
        Number of candidates to actually run in suggest_and_run mode.
    optimizer_cases : list of str or None
        Case names to run in suggest_and_run mode.
    """
    # Execute in order; stop when we hit the chosen 'until' stage.
    run_stage_runs()
    if until == "runs":
        return

    run_stage_analysis()
    if until == "analysis":
        return

    run_stage_optimizer(
        mode=optimizer_mode,
        top_k=optimizer_top_k,
        n_run=optimizer_n_run,
        cases=optimizer_cases,
    )
    # if until == "optimizer": we’re done


def main():
    parser = argparse.ArgumentParser(
        description="High-level SAM optimizer pipeline orchestrator."
    )
    parser.add_argument(
        "--until",
        type=str,
        choices=["runs", "analysis", "optimizer"],
        default="optimizer",
        help=(
            "Last stage to run: "
            "'runs' (SAM sweeps only), "
            "'analysis' (runs + csv_maker + csv_analysis), "
            "'optimizer' (full pipeline). "
            "Default: optimizer."
        ),
    )
    parser.add_argument(
        "--optimizer-mode",
        type=str,
        choices=["suggest", "suggest_and_run"],
        default="suggest",
        help=(
            "Optimizer mode for Stage 3: "
            "'suggest' (train and print ranked candidates), "
            "'suggest_and_run' (also run top N candidates). "
            "Default: suggest."
        ),
    )
    parser.add_argument(
        "--optimizer-top-k",
        type=int,
        default=10,
        help="Number of candidates to consider in the optimizer (and to display).",
    )
    parser.add_argument(
        "--optimizer-n-run",
        type=int,
        default=3,
        help="Number of candidates to actually run in suggest_and_run mode.",
    )
    parser.add_argument(
        "--optimizer-cases",
        nargs="*",
        default=None,
        help="Case names for suggest_and_run (e.g. jsalt1 jsalt2). If omitted, defaults to ['jsalt1'].",
    )

    args = parser.parse_args()
    until_stage: Stage = args.until  # type: ignore

    run_pipeline(
        until=until_stage,
        optimizer_mode=args.optimizer_mode,
        optimizer_top_k=args.optimizer_top_k,
        optimizer_n_run=args.optimizer_n_run,
        optimizer_cases=args.optimizer_cases,
    )


if __name__ == "__main__":
    main()
