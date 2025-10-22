from __future__ import annotations
import subprocess, time, pathlib, shlex, signal, sys, os

"""
Responsible for executing SAM.
Responsibilities:

Builds and launches the system command (via conda run -n SAM sam-opt -i case.i).

Streams stdout and stderr into results/runs/.../stdout.log and stderr.log.

Enforces a timeout and captures return codes.

(Optional) prints live output to the console (--live).

Writes cmdline.txt in each run directory to record the exact command used.

Returns a dictionary of metrics (wall time, exit status, etc.) to the caller.
"""

def _stream_process(proc, stdout_path, stderr_path, timeout_s, live=False):
    """Stream stdout/stderr to files; enforce timeout; return (returncode, timed_out)."""
    start = time.time()
    timed_out = False
    with open(stdout_path, "w") as out, open(stderr_path, "w") as err:
        while True:
            line = proc.stdout.readline()
            if line:
                out.write(line)
                if live:
                    print(line, end="")
            # drain stderr opportunistically
            while True:
                e = proc.stderr.readline()
                if not e:
                    break
                err.write(e)
                if live:
                    print(e, end="", file=sys.stderr)

            if proc.poll() is not None:
                # flush remainder
                rem = proc.stdout.read()
                if rem:
                    out.write(rem)
                    if live:
                        print(rem, end="")
                rem_e = proc.stderr.read()
                if rem_e:
                    err.write(rem_e)
                    if live:
                        print(rem_e, end="", file=sys.stderr)
                break

            if timeout_s is not None and (time.time() - start) > timeout_s:
                timed_out = True
                try:
                    proc.send_signal(signal.SIGINT)  # graceful
                    time.sleep(3)
                    proc.kill()                      # force
                except Exception:
                    pass
                break

            time.sleep(0.05)
    return proc.returncode if proc.returncode is not None else -9, timed_out

def run_sam(input_path, run_dir, timeout_s=3600, mock=False, sam_exe=None, extra_args=None, live=False):
    """
    Run SAM with the provided input file; stream logs; return metrics dict.
    IMPORTANT: We run inside your 'SAM' conda env (change env_name if needed).
    """
    run_dir = pathlib.Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_p = run_dir / "stdout.log"
    stderr_p = run_dir / "stderr.log"

    t0 = time.time()
    status = "ok"
    last_ts = None  # you can update this later via parsing

    if mock:
        # quick simulated run
        import random
        with open(stdout_p, "w") as out, open(stderr_p, "w") as err:
            sim_time = 0.0
            res = 1e-1
            for k in range(50):
                time.sleep(0.01)
                sim_time += 0.25
                res *= random.uniform(0.7, 0.95)
                line = f"Time Step {k}, time = {sim_time:.3f} s, Nonlinear residual: {res:.3e}\n"
                out.write(line)
                if live:
                    print(line, end="")
                last_ts = sim_time
            out.write("[PerfGraph] mock: total time 0.5 s\n")
        rc, timed_out = 0, False
    else:
        if not sam_exe:
            raise ValueError("sam_exe not provided. Pass --sam-exe or set in config.")
        if not input_path:
            raise ValueError("input_path is required for real SAM runs.")

        # --- Run inside the 'SAM' conda env (matches your manual `conda activate SAM`) ---
        env_name = "sam-o715"  # <- if your env is different (e.g., "sam-o715"), change this string.

        # Optional: live line buffering with stdbuf (Linux only). Set True if you have /usr/bin/stdbuf
        use_stdbuf = True

        cmd = ["conda", "run", "-n", env_name, "--no-capture-output"]
        if use_stdbuf:
            cmd += ["/usr/bin/stdbuf", "-oL", "-eL"]
        cmd += [sam_exe, "-i", str(input_path)]
        if extra_args:
            cmd += shlex.split(extra_args) if isinstance(extra_args, str) else list(extra_args)

        # Write the exact command for debugging/repro
        (run_dir / "cmdline.txt").write_text(" ".join(shlex.quote(c) for c in cmd) + "\n")

        proc = subprocess.Popen(
            cmd,
            cwd=str(run_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=os.environ.copy(),  # inherit current env
        )
        rc, timed_out = _stream_process(proc, stdout_p, stderr_p, timeout_s, live=live)
        if timed_out:
            status = "timeout"
        elif rc != 0:
            status = "fail"

    t1 = time.time()
    return {
        "status": status,
        "returncode": 0 if status == "ok" else (124 if status == "timeout" else rc),
        "t_wall": t1 - t0,
        "last_time_step": last_ts,
        "stdout_path": str(stdout_p),
        "stderr_path": str(stderr_p),
        "metrics": {"rmse_T": None}  # fill later
    }
