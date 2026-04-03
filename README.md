# CMB Lensing Analysis

This project computes and bins CMB lensing cross- and auto-spectra (phi–T and phi–phi) using FFP10 simulations.

## Documentation Map

Start here before editing or rerunning the analysis:

- `docs/pipeline_overview.md` - high-level pipeline stages and scientific intent
- `docs/parfiles_guide.md` - scenario/parfile/estimator mapping
- `docs/data_layout.md` - required runtime directory structure
- `docs/thesis_outputs_map.md` - notebook outputs and scenario matrix used for thesis figures
- `docs/cache_submission_workflow.md` - dependency-chained Slurm submission for PP/PT cache generation
- `docs/upstream_parallel_workflow.md` - chunked upstream scenario workflow (`qlms -> mf -> qcls -> phi_t`)
- `docs/clean_fork_workflow.md` - repository hygiene and maintenance rules

Archived planning notes:
- `docs/archive/pipeline_refactor_plan.md`

## Thesis Provenance

This table links code outputs to the corresponding parts of the thesis.

| Pipeline artifact | Notebook / script | Thesis reference |
| --- | --- | --- |
| `C_L^{\phi T}` noiseless and noisy comparison | `THESIS/PT_results.ipynb` | Theory: Section 2.6.3 (collapsed `C_L^{\phi T}`, Eqs. 52-54); Methods: Section 3.3.6 (phi-T spectrum estimation); Results: Section 4.2; Discussion: Section 5.2 |
| `C_L^{\phi\phi}` noiseless and noisy comparison | `THESIS/PP_results.ipynb` | Theory: Section 2.5.3; Methods: Section 3.3.6 (power-spectrum estimation); Results: Section 4.1; Discussion: Section 5.1 |
| Wiener filter vs delensing efficiency | `THESIS/PP_results.ipynb` and `compute_pp_plot_data.py` | Section 2.7.4 (Eqs. 63-67); Results: Figures 3, 6, 7 (Sections 4.1-4.2); Discussion: Sections 5.1-5.2 |
| Scenario matrix (lensed, input-`kappa`, MV-QEST, Pol-QEST) | `parfiles/noNoise/*`, `parfiles/Noise/*` | Methods: Section 3.3.1 (Overview of Analysis Scenarios) and Sections 3.3.3-3.3.5 |
| Amplitude summaries | `THESIS/Amplitude.ipynb` | Methods: Section 3.3.6 (phi-T amplitude fit); Results: Section 4.3; Discussion: Section 5.3 |

The operational mapping of scenarios and estimators is documented in
`docs/thesis_outputs_map.md`.

## Quick Start (Python 3.10 required)

This project ships compiled extension artifacts built against CPython 3.10 (see `*.cpython-310-*.so`), so you must use Python 3.10.x.

```bash
git clone https://github.com/daanmeerburg/Internally-Delensing-CMB-and-Estimating-A_phiT.git
cd Internally-Delensing-CMB-and-Estimating-A_phiT

# Ensure a Python 3.10 interpreter is available (examples):
#   Ubuntu 22.04+: sudo apt-get update && sudo apt-get install -y python3.10 python3.10-venv
#   pyenv:         pyenv install 3.10.14 && pyenv local 3.10.14

python3.10 -m venv venv
source venv/bin/activate
python --version  # should report 3.10.x
pip install --upgrade pip
pip install -r requirements.txt
```

## Runtime Environment

The code is expected to run under Python 3.10. On this system, `delens-env`
is the currently known working environment. If you are using that environment:

```bash
source /path/to/your/venv/bin/activate
python --version
```

If you use a different environment, keep the Python version at 3.10.x and make
sure the package set matches the requirements and any extra runtime packages you
installed manually in `delens-env`.

## Dependencies

The minimal runtime requirements (with critical pins) are in `requirements.txt`:

- numpy==1.26.4 (required build ABI for included extensions), scipy (array computing, stats; pick a version compatible with numpy 1.26.4)
- healpy (HEALPix spherical maps)
- lenspyx (lensing remapping / Wigner operations)
- matplotlib, seaborn (plotting)
- tqdm

Additional (optional) packages you may want for development / notebooks: `ipykernel`, `notebook`, `jupyterlab`.

Install extras if needed (inside the activated Python 3.10 venv):
```bash
pip install ipykernel notebook jupyterlab
python -m ipykernel install --user --name cmb-lensing
```

## Building Local Extensions

This repository should not rely on cluster-specific compiled artifacts being
tracked in Git. In particular, the `plancklens/wigners` extension should be
built locally on the target machine or cluster.

Example rebuild on the Hábrók cluster:

```bash
module load GCC/12.3.0
source /path/to/your/venv/bin/activate

export TOOLCHAIN_BIN_GCC="$EBROOTGCCCORE/bin"
export TOOLCHAIN_BIN_BINUTILS="$EBROOTBINUTILS/bin"
export PATH="$TOOLCHAIN_BIN_GCC:$TOOLCHAIN_BIN_BINUTILS:$PATH"

export CC="$TOOLCHAIN_BIN_GCC/gcc"
export CXX="$TOOLCHAIN_BIN_GCC/g++"
export FC="$TOOLCHAIN_BIN_GCC/gfortran"
export F77="$FC"
export F90="$FC"

cd plancklens/wigners
python -m numpy.f2py --fcompiler=gnu95 -c -m wigners wigners.f90
```

If you run on a different system, adapt the compiler and module setup accordingly.

## Environment Configuration

Edit or create `env_config.py` to define paths (example values shown):
```python
import os

PLENS = os.environ.get("PLENS", "/absolute/path/to/output/")
INPUT = os.environ.get("INPUT", "/absolute/path/to/input/")
PARAMS = os.environ.get("PARAMS", "./input")  # contains mask.fits.gz, dcl_sim, dcl_dat
KFIELD = os.environ.get("KFIELD", "/absolute/path/to/kappa_fields/")
```

Meaning of variables:
- PLENS: Output directory root (will store generated spectra / intermediates)
- INPUT: Directory with simulation CMB maps `cmb_%05d.fits`, noise maps `noise_%05d.fits`, and data map `SMICA.fits`
- PARAMS: Directory holding mask and dCl spectrum inputs (already includes small sample files here)
- KFIELD: Directory for lensing kappa `klm_%03d.fits` inputs if used

You can also export these as environment variables before running scripts instead of editing the file.

Example cluster-style configuration:

```bash
export PLENS=/path/to/your/runtime-root/PLENS
export INPUT=/path/to/your/runtime-root/INPUT
export PARAMS=/path/to/your/repo/input
export KFIELD=/path/to/your/runtime-root/KFIELD
```

## Data Layout (expected)

```
<INPUT>/cmb_00000.fits
<INPUT>/cmb_00001.fits
... (CMB sims)
<INPUT>/noise_00000.fits
<INPUT>/noise_00001.fits
... (noise sims)
<KFIELD>/klm_000.fits
<KFIELD>/klm_001.fits
... (input lensing)
<INPUT>/SMICA.fits           # data map
<PARAMS>/mask.fits.gz        # analysis mask
<PARAMS>/dcl_sim             # sim power adjustment
<PARAMS>/dcl_dat             # data power adjustment
```

The scratch-oriented layout and the downloader workflow are documented in
`docs/data_layout.md`.

## Running the Pipeline

Generate spectra and intermediate products:
```bash
source /path/to/your/venv/bin/activate
python run_parfiles.py
```

You can customize which "parameter set" to run by editing imports inside
`run_parfiles.py` or the modules under `parfiles/`. The current driver processes
an explicit list of `(parfile, estimator)` pairs through `main()`.

## Notebooks

After generating results, explore the notebooks in `THESIS/`:
- `Amplitude.ipynb` – Lensing amplitude vs. simulations
- `Carron_2017.ipynb` – Reproduction of literature results
- `PP_results.ipynb` – Phi–phi auto-spectrum
- `PT_results.ipynb` – Phi–T cross-spectrum
