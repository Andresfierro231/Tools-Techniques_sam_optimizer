"""
run_launcher.py

Run orchestration for a single SAM run.

Main entry point:

    run_sam_case(case_name, template_name, hyperparams)

This will:
  1. Build a unique input .i file from the given template, applying
     hyperparameters (node_multiplier, order, etc.) via text replacement.
  2. Start a run context via runtime_logger.
  3. Invoke the SAM executable with a timeout (from CONFIG["runtime_limits"]).
  4. Record success/fail/timeout in runtimes_master.csv.
  5. Return a small summary dict for convenience.

This module does NOT compute error metrics or do any ML.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from .config import CONFIG
from . import runtime_logger


def _repo_root() -> Path:
    """
    Guess the active_development root by going one level up from this file.
    (sam_opt is inside active_development.)
    """
    return Path(__file__).resolve().parent.parent


def _load_template(template_name: str) -> str:
    """Read the contents of a template .i file."""
    templates_dir = Path(CONFIG["paths"]["templates_dir"]).resolve()
    template_path = templates_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text(), template_path

def _apply_hyperparams_to_text(text: str, hyperparams: Dict[str, Any]) -> str:
    """
    Apply hyperparameters as text replacements in the SAM input file.

    Right now this does:
      - node_multiplier := <node_multiplier>
      - quad_order := FIRST/SECOND based on 'order'
      - p_order_quadPnts := 1 or 2 (matching 'order')

    We can extend this later for IC/BC knobs (e.g. HTC, inlet temperatures).

    NOTE: This assumes the template has lines like:
        node_multiplier := 8
        quad_order := FIRST
        p_order_quadPnts := 1
    """
    new_text = text

    # node_multiplier
    if "node_multiplier" in hyperparams:
        nm = int(hyperparams["node_multiplier"])
        # Use a lambda to avoid the \1N backref ambiguity
        new_text = re.sub(
            r"(node_multiplier\s*:=\s*)\S+",
            lambda m: f"{m.group(1)}{nm}",
            new_text,
        )

    # order (1 or 2), controlling quad_order and p_order_quadPnts
    if "order" in hyperparams:
        order = int(hyperparams["order"])
        quad_str = "FIRST" if order == 1 else "SECOND"

        # quad_order
        new_text = re.sub(
            r"(quad_order\s*:=\s*)\S+",
            lambda m: f"{m.group(1)}{quad_str}",
            new_text,
        )

        # p_order_quadPnts
        new_text = re.sub(
            r"(p_order_quadPnts\s*:=\s*)\S+",
            lambda m: f"{m.group(1)}{order}",
            new_text,
        )

    # HTC or other IC/BC knobs can be wired in here later, e.g.:
    # if "htc" in hyperparams:
    #     htc_val = float(hyperparams["htc"])
    #     new_text = re.sub(
    #         r"(some_htc_param\s*:=\s*)\S+",
    #         lambda m: f"{m.group(1)}{htc_val}",
    #         new_text,
    #     )

    return new_text



def _build_input_filename(template_name: str, hyperparams: Dict[str, Any]) -> str:
    """
    Build a concrete .i filename from the template name and hyperparams.

    To remain compatible with your existing csv_maker/csv_analysis pipeline,
    we PRESERVE the 'nodes_mult_by_<N>' pattern in the filename.

    Example:
      template_name = "jsalt1.i", hyperparams["node_multiplier"] = 24
      -> "jsalt1_nodes_mult_by_24_ord2_htc1000.i"

    If node_multiplier is not given, we fall back to a generic suffix.
    """
    stem = Path(template_name).stem  # e.g. "jsalt1"
    parts = [stem]

    nm = hyperparams.get("node_multiplier")
    if nm is not None:
        parts.append(f"nodes_mult_by_{int(nm)}")
    else:
        parts.append("nodes_mult_by_unknown")

    # Optional extra tags for readability (analysis still finds nodes_mult_by_XX)
    order = hyperparams.get("order")
    if order is not None:
        parts.append(f"ord{int(order)}")

    htc = hyperparams.get("htc")
    if htc is not None:
        parts.append(f"htc{int(htc)}")

    return "_".join(parts) + ".i"


def run_sam_case(
    case_name: str,
    template_name: str,
    hyperparams: Dict[str, Any],
    timeout_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run a single SAM case given a template and hyperparameters.

    Parameters
    ----------
    case_name : str
        Logical name of the experiment (e.g. "jsalt1").
        This is passed through to the runtime log as the 'case' field.
    template_name : str
        Template .i filename located in CONFIG["paths"]["templates_dir"].
        Example: "jsalt1.i"
    hyperparams : dict
        Hyperparameters / IC-BC knobs. For now expects:
            - node_multiplier (int)
            - order (int: 1 or 2)
            - (optional) htc, etc.
    timeout_sec : float or None
        If None, uses CONFIG["runtime_limits"]["absolute_sec"].
        Otherwise overrides the global default for this run.

    Returns
    -------
    dict
        Summary of the run as logged by runtime_logger.end_run().
    """
    repo_root = _repo_root()
    templates_dir = Path(CONFIG["paths"]["templates_dir"]).resolve()

    # 1) Read template
    template_text, template_path = _load_template(template_name)

    # 2) Apply hyperparameters to text
    modified_text = _apply_hyperparams_to_text(template_text, hyperparams)

    # 3) Build concrete input filename
    concrete_name = _build_input_filename(template_name, hyperparams)
    concrete_path = templates_dir / concrete_name
    concrete_path.write_text(modified_text)

    # 4) Prepare run context
    output_dir = repo_root  # for now we keep outputs in the existing structure
    run_ctx = runtime_logger.start_run(
        case=case_name,
        hyperparams=hyperparams,
        sam_input_path=str(concrete_path),
        output_dir=str(output_dir),
    )

    # 5) Figure out timeout
    if timeout_sec is None:
        timeout_sec = float(CONFIG["runtime_limits"]["absolute_sec"])

    sam_exec = CONFIG["paths"]["sam_executable"]
    cmd = [sam_exec, "-i", str(concrete_path)]

    # Log file for stdout/stderr (optional but useful)
    log_file_path = concrete_path.with_suffix(".log")

    try:
        with log_file_path.open("w") as logf:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_root),
                stdout=logf,
                stderr=subprocess.STDOUT,
                timeout=timeout_sec,
                check=False,
            )
        status = "success" if proc.returncode == 0 else "fail"
        return_code = proc.returncode
        timeout_used = timeout_sec if status == "timeout" else None

    except subprocess.TimeoutExpired:
        # If SAM runs longer than timeout_sec, we kill it and mark as timeout
        status = "timeout"
        return_code = None
        timeout_used = timeout_sec

    # 6) Finalize logging
    logged_row = runtime_logger.end_run(
        run_ctx,
        status=status,
        return_code=return_code,
        timeout_sec=timeout_used,
    )

    # 7) Augment logged_row with some extra fields for convenience
    logged_row["sam_input_path"] = str(concrete_path)
    logged_row["log_file_path"] = str(log_file_path)

    return logged_row
