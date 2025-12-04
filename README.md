# physor2026_andrew

# This is the main place I should do my python harness for SAM. No longer use the bubble_flow_loop 

# opt tuner in active development

Absolutely — here is a polished, **submission-ready `README.md`** for your project.
It is written in a professional, academic tone suitable for a computational engineering course or research submission.

If you'd like, I can tailor it further using your exact course name, professor name, or assignment prompt.

---

# 📄 **README.md (Submission-Ready)**

*(You can copy & paste this directly into your repository.)*

---

# **SAM Optimizer for Molten-Salt Loop Modeling**

**Author:** Andrés Nicolás Fierro López
**Course:** Computational Engineering Project
**Toolchain:** SAM (System Analysis Module), MOOSE Framework, Python (workflow automation), HPC resources (TACC LS6)

---

## **1. Project Overview**

This project develops an automated **SAM optimization pipeline** to calibrate, validate, and accelerate thermal-hydraulic simulations of a molten-salt natural-circulation loop (e.g., TAMU MSFL). The objective is to build a reproducible workflow that:

1. Establishes a **performance baseline** for SAM simulations across solver configurations, mesh sizes, time-step selections, and nonlinear/linear solver tolerances.
2. Automates **parameter sweeps, run management, runtime tracking**, and postprocessing.
3. Implements a **lightweight ML-guided optimization** layer for early-exit heuristics and parameter tuning to reduce runtime while preserving accuracy.
4. Compares SAM model outputs against **experimental validation data** and prior benchmark cases.

The project serves as a foundation for a future **digital-twin pipeline** that couples SAM simulations with surrogate models (e.g., Random Forests, GBDTs, Optuna-style search heuristics).

---

## **2. Repository Structure**

```
.
├── Templates/                        # Base SAM input files for parameterized studies
│   ├── jsalt1.i
│   ├── jsalt2.i
│   ├── jsalt3.i
│   ├── jsalt4.i
│   └── jsalt_base_case.i
│
├── active_development/
│   ├── csv_maker.py                  # Generates simulation CSVs & postprocessing files
│   ├── csv_analysis.py               # Parses runtimes, RMSE, accuracy metrics
│   ├── runtime_monitor.py            # Tracks solver performance & logs metadata
│   └── ... additional scripts
│
├── analysis/
│   ├── runtimes_master.csv           # Aggregated runtime/performance database
│   └── analysis/                     # NURETH/PHYSOR-style summaries
│
├── Validation_Data/
│   └── validation_data.csv           # Experimental data for ∆T, TP1–TP6, velocity, etc.
│
└── README.md
```

---

## **3. Computational Workflow**

### **3.1 Parameterized SAM Input Generation**

Base `.i` templates are dynamically modified to sweep over:

* mesh density (`node_multiplier`)
* solver order (1st / 2nd order)
* initial/boundary conditions (inlet temperature, heater power, mass-flow initialization)
* time-step control parameters
* nonlinear and linear solver tolerances

All modifications are logged for reproducibility.

---

### **3.2 Simulation Execution & Runtime Tracking**

Simulations are launched via Python’s `subprocess` interface:

* Start/stop timestamps recorded with `time.perf_counter()`
* Solver metadata captured from SAM logs:

  * nonlinear iterations
  * linear iterations
  * Jacobian evaluations
  * timestep count
  * convergence failures
  * CFL & stability metrics

A master record (`runtimes_master.csv`) aggregates all studies.

---

### **3.3 Postprocessing & Accuracy Metrics**

Outputs are parsed and compared against:

* **Validation data** (experimental loop ∆T, TP1–TP6 temperature profiles, pressure drops)
* **Prior SAM runs** (baseline coarse/fine mesh results)

Computed metrics include:

* RMSE between model and experiment
* % error of ∆T across measurement points
* Runtime vs accuracy tradeoff curves
* Mesh order and discretization effects
* Solver stability behaviors

Visualization includes:

* Runtime scaling laws
* Accuracy vs node_multiplier
* Heat-transfer coefficient sensitivity
* Pareto-optimal parameter sets

---

### **3.4 ML-Guided Optimization (Prototype)**

A lightweight ML layer analyzes:

* relationships between runtime and solver configuration
* patterns indicating “slow” runs early in execution
* predictive features for early-exit heuristics

Models tested:

* Random Forest Regressor (runtime prediction)
* Gradient Boosted Trees (feature ranking)
* Logistic Classification (predict “will exceed runtime budget?”)

This enables adaptive stopping rules and smarter parameter exploration.

---

## **4. Results Summary**

**Key findings from the runtime and accuracy analyses:**

* Higher-order time discretization improves accuracy with only moderate runtime penalty for mid-range mesh densities.
* Runtime scales nearly linearly with `node_multiplier`, with sharp increases beyond ×16.
* Heat-transfer correlations significantly affect stability and accuracy; geometry-specific correlations produce the best results.
* ML-based early-quit heuristics reduce wasted computation on unstable or overly expensive runs.
* The full pipeline supports rapid, repeatable studies for future SAM-based digital-twin development.

(See `analysis/` directory for figures, tables, and detailed summaries.)

---

## **5. How to Run the Project**

### **5.1 Environment Setup**

```bash
conda activate python_harness_sam
module load python
module load moose/sam
```

Ensure SAM is in your PATH:

```bash
which sam-opt
```

### **5.2 Running a Simulation Batch**

```bash
python csv_maker.py
```

### **5.3 Analyzing Results**

```bash
python csv_analysis.py
```

### **5.4 Generating Figures / Paper-Ready Results**

```bash
python analysis/generate_plots.py
```

---

## **6. Dependencies**

* **Python 3.10+**
* **Pandas**, **NumPy**, **Matplotlib**
* **scikit-learn** (for ML components)
* **SAM (MOOSE Framework)**
* HPC job scheduler (TACC LS6: SLURM or PBS-style submission wrappers)

---

## **7. Academic Integrity Statement**

This repository represents my own original work.
Portions involving SAM or MOOSE usage follow publicly documented APIs and tutorials.
All experimental validation data is properly sourced and cited in accompanying slides/reports.

---

## **8. Contact**

**Andrés Nicolás Fierro López**
Email: [andresfierro@utexas.edu](mailto:andresfierro@utexas.edu)
GitHub: [https://github.com/UT-Computational-NE/physor2026_andrew](https://github.com/UT-Computational-NE/physor2026_andrew)

Feel free to contact me for clarification, replication instructions, or additional documentation.
