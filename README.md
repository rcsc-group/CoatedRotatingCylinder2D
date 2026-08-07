# Coated rotating cylinder in two dimensions

Direct numerical simulation infrastructure for the two-dimensional evolution of a liquid coating on a rotating cylinder. The implementation is based on [Basilisk C](https://basilisk.fr/) and combines adaptive mesh refinement, volume-of-fluid interface tracking, two-phase Navier--Stokes dynamics, surface tension, gravity, automated parameter sweeps, performance profiling, and publication-oriented post-processing.

This repository is intended to provide a compact and reproducible computational companion to the associated study available at [https://doi.org/10.1017/jfm.2020.421](https://doi.org/10.1017/jfm.2020.421), bringing together mathematical modelling, asymptotic analysis, reduced-dimensional modelling calculations and direct numerical simulation towards resolving the delicate interplay between forces found in the (highly nonlinear) dynamics of a liquid film coating a rotating cylinder, inspired by the so-called *honey dipper problem* elegantly presented by [H. K. Moffatt in 1977](https://www.damtp.cam.ac.uk/user/hkm2/PDFs/Moffatt_1977_JM_16_651.pdf). It supports collaborative work with [Dr. Alexander W. Wray](https://alexwray.co.uk/#!/) at the University of Strathclyde, whom I am grateful to for bringing this problem to my attention back in 2018 and for fantastic discussions on this topic since then.

<img width="500" height="500" alt="centre_of_mass_trajectory" src="https://github.com/user-attachments/assets/7a8c4402-b54f-466b-a6ce-8fc1881ffcd7" />

---

## 📌 Features

✅ Two-dimensional incompressible two-phase Navier--Stokes solver  
✅ Volume-of-fluid representation of the liquid--gas interface  
✅ Surface tension, gravity, density contrast, and viscosity contrast  
✅ Rotating unit-radius cylinder with an initially prescribed coating thickness  
✅ Adaptive quadtree refinement with configurable maximum AMR level  
✅ Automated sweeps over film radius, rotation coefficient, and resolution  
✅ Centre-of-mass convergence criterion for automatic run termination  
✅ Persistent liquid-film rupture diagnostic based on connected components  
✅ Interface, diagnostic, snapshot, and animation output  
✅ Optional Basilisk `TRACE` and Linux `perf` profiling  
✅ Python post-processing for coating thickness and spatial trajectories  
✅ Reproducibility metadata, timing information, exit status, and source checksum

---

## 🌊 Physical and numerical model

The principal simulation is contained in `CoatedCylinder.c`. It models a liquid film coating the exterior of a rotating circular cylinder in a surrounding gas. The flow is solved using Basilisk's centred incompressible Navier--Stokes formulation together with volume-of-fluid interface tracking and surface tension.

The principal runtime parameters are:

- film-radius parameter `fRadius`;
- dimensionless cylinder-rotation coefficient `cV`;
- maximum adaptive-mesh level `MAX_LEVEL`.

The cylinder radius is nondimensionalised to unity. The calculation uses adaptive quadtree refinement and tracks the liquid centre of mass, coating-thickness extrema, connected liquid components, and saved interfaces throughout the run.

<!-- TODO: Add the exact nondimensionalisation and manuscript-specific dimensionless groups. -->

---

## 🛠️ Installation

### 1. Requirements

The simulation workflow requires:

- [Basilisk C](https://basilisk.fr/) with `qcc`;
- a C compiler with OpenMP support;
- GNU `make`;
- `/usr/bin/time`;
- optional visualisation utilities such as `ffmpeg`, ImageMagick, and `gnuplot`;
- optional Linux `perf` for hardware-counter profiling.

On a Debian/Ubuntu-like system, useful supporting packages include:

```sh
sudo apt install build-essential gnuplot imagemagick ffmpeg
```

### 2. Clone the repository

```sh
git clone https://github.com/rcsc-group/CoatedRotatingCylinder2D
cd CoatedRotatingCylinder2D
```

### 3. Install and configure Basilisk

Follow the official [Basilisk installation instructions](https://basilisk.fr/src/INSTALL).

The supplied runner expects the `BASILISK` environment variable to point to the Basilisk source directory and `qcc` to be available on `PATH`. A typical setup is:

```sh
export BASILISK=$HOME/basilisk/src
export PATH=$PATH:$BASILISK
```

It is convenient to place these lines in `~/.bashrc` or the equivalent startup file for your shell.

---

## ▶️ Running the simulations

Move to the driver-code directory:

```sh
cd DriverCode
```

### Single case

A standard production run at maximum AMR level 10 can be launched with:

```sh
TRACE_LEVEL=0 \
USE_PERF=0 \
OMP_NUM_THREADS=4 \
MAX_LEVEL=10 \
sh run_cylinder.sh
```

### Resolution study

Whitespace-separated values are interpreted as parameter lists:

```sh
TRACE_LEVEL=0 \
USE_PERF=0 \
OMP_NUM_THREADS=4 \
MAX_LEVEL="7 8 9 10 11" \
OUTROOT="output" \
sh run_cylinder_sweep.sh
```

The source is compiled once and one simulation is launched for each requested resolution.

### General parameter sweep

The same mechanism applies to the film radius and cylinder velocity:

```sh
FRADIUS="1.25 1.5 1.75" \
CV="0.5 1.0" \
MAX_LEVEL="8 9 10" \
TRACE_LEVEL=0 \
USE_PERF=0 \
OMP_NUM_THREADS=4 \
OUTROOT="output" \
sh run_cylinder.sh
```

This executes the Cartesian product of all supplied values.

Each case is written to a directory of the form

```text
fR_<fRadius>_cV_<cV>_L_<MAX_LEVEL>
```

for example:

```text
fR_1.5_cV_1.0_L_10
```

---

## ⚙️ Execution and profiling controls

| Variable | Purpose | Typical production value |
|---|---|---:|
| `FRADIUS` | Film-radius value or whitespace-separated sweep | `1.5` |
| `CV` | Cylinder-rotation coefficient or sweep | `1.0` |
| `MAX_LEVEL` | Maximum AMR level or sweep | `10` |
| `OMP_NUM_THREADS` | Number of OpenMP threads | machine/problem dependent |
| `OUTROOT` | Root simulation-output directory | `output` |
| `TRACE_LEVEL` | Basilisk event/function tracing | `0` |
| `USE_PERF` | Linux hardware-counter collection | `0` |

For profiling runs:

```sh
TRACE_LEVEL=2 USE_PERF=auto sh run_cylinder.sh
```

For clean production timing:

```sh
TRACE_LEVEL=0 USE_PERF=0 sh run_cylinder.sh
```

`USE_PERF=1` can be used when hardware counters are required and the run should fail rather than silently continue when `perf` is unavailable.

> [!NOTE]
> OpenMP scaling is problem- and resolution-dependent. Small adaptive grids may not benefit from a large thread count. Benchmark representative cases before selecting the production value of `OMP_NUM_THREADS`.

> [!NOTE]
> Compiler optimisation flags are configurable through the runner. If `-march=native` is enabled, compile the executable on a machine with the same CPU architecture as the machine on which it will run.

---

## 📁 Repository structure

```text
.
├── CoatedCylinder.c
├── run_cylinder.sh
├── run_cylinder_sweep.sh
│
├── plot_com_trajectory.py
├── plot_com_trajectory_resolution.py
├── plot_thickness.py
├── plot_thickness_resolution.py
├── postprocess_common.py
│
├── output/
│   └── fR_1.5_cV_1.0_L_10/
│       └── ...
│
├── LICENSE
└── README.md
```

The repository is deliberately kept compact:

- `CoatedCylinder.c` contains the Basilisk simulation.
- `run_cylinder.sh` provides the standard single-case/benchmark workflow.
- `run_cylinder_sweep.sh` manages parameter and resolution sweeps.
- `postprocess_common.py` contains the shared Python analysis utilities.
- `plot_*.py` scripts generate single-case and resolution-comparison figures.
- `output/` contains a representative simulation output using the same directory convention produced by the sweep workflow.
  
The files in this repository and their organisation represent a minimal working version of the implementation, which encompasses the necessary ingredients for reproducibility, as well as sample output (in the sense of only a subset of the files being uploaded while trying to strike the balance between the framework being informative and compact). Once familiarity with the codebase has been reached, the following structure for the codebase is recommended:

```text
.
├── DriverCode/
│   ├── CoatedCylinder.c
│   └── run_cylinder.sh
│
├── PostProcessing/
│   ├── postprocess_common.py
│   ├── plot_thickness.py
│   ├── plot_thickness_resolution.py
│   ├── plot_com_trajectory.py
│   ├── plot_com_trajectory_resolution.py
│   └── README.md
│
├── Figures/
│   └── ...
│
├── SupplementaryMovies/
│   └── ...
│
├── LICENSE
└── README.md
```

`DriverCode/` contains the simulation and execution workflow. `PostProcessing/` contains the reusable Python analysis suite. `Figures/` and `SupplementaryMovies/` are natural locations for representative visualisations or outward-facing material in general.

---

## 📊 Simulation output

A parameter sweep produces a top-level output directory containing the compiled executable, build metadata, a sweep summary, and one directory per parameter combination:

```text
output/
├── CoatedCylinder
├── build-metadata.txt
├── sweep-summary.tsv
│
├── fR_1.5_cV_1.0_L_9/
│   ├── Animations/
│   ├── Interfaces/
│   ├── Slices/
│   ├── logdroplets.dat
│   ├── logstats.dat
│   ├── logvol.dat
│   ├── perfs
│   ├── rupture.flag
│   ├── stdout.log
│   ├── stderr.log
│   ├── time.txt
│   ├── event-profile.txt
│   ├── exit-status.txt
│   └── metadata.txt
│
└── fR_1.5_cV_1.0_L_10/
    └── ...
```

The most useful diagnostic outputs are:

- `logvol.dat` — film-volume and minimum/maximum thickness diagnostics;
- `logdroplets.dat` — connected-component and centre-of-mass diagnostics;
- `Interfaces/` — saved liquid-interface coordinates;
- `rupture.flag` — persistent `0/1` indicator recording whether multiple connected liquid components were detected;
- `perfs` — Basilisk performance history;
- `time.txt` — GNU `time -v` resource summary;
- `event-profile.txt` — Basilisk `TRACE=2` profile when enabled;
- `metadata.txt` — case-level parameters and execution settings;
- `exit-status.txt` — simulation process exit status.

At sweep level, `sweep-summary.tsv` provides a compact overview of the parameter combination, exit status, and rupture classification for each case.

---

## 🐍 Post-processing

The Python suite reconstructs coating-thickness histories, centre-of-mass trajectories, tracked maximum-thickness trajectories, final liquid interfaces, and resolution comparisons.

### Python environment

From the `PostProcessing/` directory, create a local virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
```

Install the required Python packages:

```sh
python3 -m pip install --upgrade pip
python3 -m pip install numpy matplotlib pylustrator
```

The environment only needs to be created once. In later sessions:

```sh
. .venv/bin/activate
```

To leave it:

```sh
deactivate
```

### Standard plotting commands

For a single resolution:

```sh
python3 plot_thickness.py --level 10
python3 plot_com_trajectory.py --level 10
```

For a resolution study:

```sh
python3 plot_thickness_resolution.py --levels 7 8 9 10 11
python3 plot_com_trajectory_resolution.py --levels 7 8 9 10 11
```

A different simulation root can be supplied explicitly:

```sh
python3 plot_thickness_resolution.py \
  --output-root /path/to/output \
  --levels 7 8 9 10 11
```

For non-interactive execution:

```sh
python3 plot_thickness.py --level 10 --save-only
```

If external LaTeX rendering is unavailable:

```sh
python3 plot_thickness.py --level 10 --save-only --no-tex
```

The plotting scripts export publication-quality PDF files together with high-resolution PNG versions.

---

## 🔬 Reproducibility and performance information

The execution workflow records the numerical case parameters together with compiler, OpenMP, tracing, timing, and source-version information. Useful metadata include:

- compiler and optimisation flags;
- OpenMP thread count and placement settings;
- requested parameter sweep;
- source SHA-256 checksum;
- tracing and hardware-counter configuration.

Performance measurements should distinguish between:

- **production timing** — `TRACE_LEVEL=0`, `USE_PERF=0`;
- **Basilisk hotspot profiling** — `TRACE_LEVEL=2`;
- **hardware-counter profiling** — `USE_PERF=1`.

Instrumentation can affect runtime, so profiling and clean timing results should not be treated as directly interchangeable.

---

## 📚 Citation

If you use this code or associated data in your work, please cite the accompanying publication:

> Wray, A. W., & Cimpeanu, R. (2020). Reduced-order modelling of thick inertial flows around rotating cylinders. Journal of Fluid Mechanics, 898, A1.

BibTeX:
```bibtex
@article{wray2020reduced,
  title={Reduced-order modelling of thick inertial flows around rotating cylinders},
  author={Wray, Alexander W and Cimpeanu, Radu},
  journal={Journal of Fluid Mechanics},
  volume={898},
  pages={A1},
  year={2020},
  publisher={Cambridge University Press}
}
```

---

## 🤝 Contributing

Contributions and reproducibility feedback are welcome. Please feel free to:

- open an issue for bugs, portability problems, or questions;
- fork the repository;
- submit a pull request for a well-tested improvement.

For numerical changes, please document any modifications to solver tolerances, mesh-adaptation criteria, physical parameters, compiler settings, or stopping conditions that may affect reproducibility.

---
