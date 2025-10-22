# sam-opt-starter

Starter scaffold for **SAM optimization experiments** with:
- Durable SQLite run registry (append-only)
- Streaming-friendly `runner` (mock mode included)
- Simple CLI to run a single experiment and log metrics
- Configs, docs, and repo structure aligned to your project plan

## Quick start

```bash
# 1) (optional) create venv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Dry run in mock mode (no SAM needed)
python -m bin.sam_run --params configs/example_params.json --mock --note "first dry run"

# 4) Inspect registry
python -m bin.inspect_registry
```

Artifacts are stored under `results/runs/<run_id>/` and a durable SQLite DB `results/samopt.sqlite` is maintained.
