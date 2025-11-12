from __future__ import annotations
import argparse, json, pathlib, time
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from sam_tools.config import load_yaml, ensure_results_dir
from sam_tools.params import stable_hash
from sam_tools.registry import insert_run
from sam_tools.runner import run_sam

"""Main CLI tool to launch one SAM case and record results.
Responsibilities:

Parse command-line arguments (--params, --template, --note, etc.).

Render the Jinja2 SAM input template (case.i) using parameters from JSON.

Create a timestamped run folder under results/runs/.

Call sam_tools.runner.run_sam() to actually execute SAM or run a mock simulation.

Insert a structured record of the run into the SQLite registry for traceability.

Print a short summary at the end.
"""

def render_input(template_path: str, run_dir: pathlib.Path, params: dict) -> pathlib.Path:
    tpl_path = pathlib.Path(template_path).resolve()
    env = Environment(
        loader=FileSystemLoader(str(tpl_path.parent)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(tpl_path.name)
    text = tpl.render(**params)
    out_path = run_dir / "case.i"
    out_path.write_text(text)
    return out_path

def main():
    ap = argparse.ArgumentParser(description="Run a single SAM job and log metrics")
    ap.add_argument("--params", required=True, help="JSON file with parameters")
    ap.add_argument("--config", default="configs/experiment.yaml", help="YAML experiment config")
    ap.add_argument("--phase", default="baseline", help="phase label: baseline|icbc|htc")
    ap.add_argument("--note", default="", help="free-form note stored in registry")
    ap.add_argument("--mock", action="store_true", help="run in mock mode (no SAM)")
    ap.add_argument("--sam-exe", default=None, help="Path to SAM executable (overrides config)")
    ap.add_argument("--template", default="configs/base_input_template.i", help="Path to Jinja2 SAM input template")
    ap.add_argument("--live", action="store_true", help="also print SAM output to console")
    ap.add_argument("--extra-args", default=None, help="Extra CLI args to pass to SAM (string)")
    args = ap.parse_args()

    params = json.loads(pathlib.Path(args.params).read_text())
    cfg = load_yaml(args.config)

    # Compute a simple hash for caching or traceability
    run_id = time.strftime("%Y%m%dT%H%M%S")
    params_hash = stable_hash(params)

    # Per-run artifacts
    runs_root = ensure_results_dir("results/runs")
    run_dir = runs_root / f"{run_id}_{params_hash}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Save params for reproducibility
    (run_dir / "params.json").write_text(json.dumps(params, indent=2))

    # Resolve executable and render input (real mode)
    sam_exe = args.sam_exe or (cfg.get("sam_exe") if cfg else None)
    input_path = None
    if not args.mock:
        input_path = render_input(args.template, run_dir, params)
        input_for_runner = "case.i"

    # Execute run
    result = run_sam(
        input_path=input_for_runner,
        run_dir=run_dir,
        timeout_s=cfg.get("timeout_s", 3600),
        mock=args.mock,
        sam_exe=sam_exe,
        extra_args=args.extra_args,
        live=args.live                   # <-- add this

    )

    # Prepare record
    now_ts = time.time()
    record = {
        "run_id": run_id,
        "phase": args.phase,
        "sam_input_hash": params_hash,
        "params": params,
        "features": {},  # fill with scenario features later
        "status": result["status"],
        "metrics": {"t_wall": result["t_wall"], "rmse_T": result["metrics"].get("rmse_T")},
        "t_start": now_ts - result["t_wall"],
        "t_end": now_ts,
        "artifacts_dir": str(run_dir),
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "notes": args.note
    }
    insert_run(record)

    print(f"Run complete: {record['status']} | rc={result['returncode']} | t_wall={record['metrics']['t_wall']:.3f}s")
    print(f"Input : {input_path if input_path else '(mock)'}")
    print(f"Logs  : {record['stdout_path']}  |  {record['stderr_path']}")
    print(f"Artifacts: {record['artifacts_dir']}")

if __name__ == "__main__":
    main()
