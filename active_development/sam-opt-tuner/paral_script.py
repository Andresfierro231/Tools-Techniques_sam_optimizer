import os, time, subprocess, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

node_mult_list = [3, 6, 12, 24, 48, 96, 100, 200]
prefixes = ["jsalt", "jwater"]      # ← run both families
indices  = [1, 2, 3, 4]
MAX_WORKERS = min(4, (os.cpu_count() or 4))

def make_outfile(inputfile: str, outfile: str, node_mult: int) -> None:
    with open(inputfile, "r") as f_in, open(outfile, "w") as f_out:
        for line in f_in:
            if "node_multiplier" in line:
                f_out.write(f"node_multiplier := {node_mult}\n")
            else:
                f_out.write(line)

def run_case(prefix: str, i: int, node_mult: int):
    """
    Returns: (prefix, i, outfile, elapsed, error_log_path_or_None)
    """
    inputfile = f"{prefix}{i}.i"
    outfile   = f"{prefix}{i}_nodes_mult_by_{node_mult}.i"
    make_outfile(inputfile, outfile, node_mult)

    start = time.time()
    cmd = ["sam_lite_container_execute","sam-opt", "-i", outfile]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".log", mode="w") as logf:
        tmp_path = logf.name
        proc = subprocess.Popen(cmd, stdout=logf, stderr=logf, text=True)
        proc.wait()
    elapsed = time.time() - start

    if proc.returncode == 0:
        os.remove(tmp_path)
        return prefix, i, outfile, elapsed, None
    else:
        final_log = f"{outfile}.txt"
        with open(tmp_path, "a") as logf:
            logf.write(f"\n# Script runtime: {elapsed:.3f} seconds\n")
        shutil.move(tmp_path, final_log)
        return prefix, i, outfile, elapsed, final_log

for node_mult in node_mult_list:
    print(f"\n=== node_multiplier = {node_mult} ===")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {
            ex.submit(run_case, prefix, i, node_mult): (prefix, i)
            for prefix in prefixes for i in indices
        }
        for fut in as_completed(futures):
            prefix, i, outfile, elapsed, log = fut.result()
            tag = f"{prefix}{i}"
            if log is None:
                print(f"[OK] {tag} → {outfile} ({elapsed:.2f}s)")
            else:
                print(f"[ERROR] {tag} → {outfile} ({elapsed:.2f}s) | log: {log}")

