# Experiment Charter – Phase 0

**Title:** Baseline SAM Case for Automated Parameter Optimization  
**Author:** YOUR NAME  
**Date:** YYYY-MM-DD  

## 1. Representative Model
- SAM input: `WaterLoop_Case01.i`
- Physical system: natural-circulation water loop (TAMU MSFL analog)
- Runtime: ~25 min on laptop (8 threads)
- Validation: TAMU loop data, steady-state ΔT and pressure drop

## 2. Machines / Software
| Item | Specification |
|------|----------------|
| Hardware | YOUR MACHINE |
| OS | |
| SAM build | v20XX.XX (RelWithDebInfo) |
| Python env | `sam-opt` (3.11, pandas, psutil) |

## 3. Metrics to Track
| Metric | Description / Extraction |
|---------|-------------------------|
| Wall-clock time | `time` or SAM perf log |
| Nonlinear iterations | from SAM stdout |
| Linear iterations | from SAM stdout |
| Max memory | `/usr/bin/time -v` |
| Success flag | convergence true/false |
| RMSE(T,P) | vs experimental data |

## 4. Tunable Parameters
| Parameter | Symbol | Range | Notes |
|------------|---------|-------|-------|
| IC temperature offset | ΔTᵢ꜀ | [−10, +10 K] | sensitivity |
| IC mass-flow scale | αₘ | [0.9, 1.1] |  |
| BC hot-leg offset | ΔTₕ | [−5, +5 K] |  |
| HTC multiplier | βₕₜ꜀ | [0.7, 1.5] |  |
| Friction factor multiplier | β_f | [0.7, 1.5] |  |
| Solver tolerance | ε | [1e-5, 1e-3] |  |
| Preconditioner | P | {AMG, ILU} |  |

## 5. Success Criteria
- Charter approved by mentors / professors  
- Baseline SAM case reproduces experimental ΔT within ±5 %  
- All listed metrics extractable automatically via Python parser  

## 6. Deliverable
`docs/experiment_charter.md`
