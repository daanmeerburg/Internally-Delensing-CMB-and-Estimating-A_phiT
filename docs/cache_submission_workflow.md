# Cache Submission Workflow

This workflow submits PP/PT thesis-cache jobs with explicit Slurm
dependencies, so you do not need to manually sequence all scenarios.

## Prerequisites

- Runtime directories populated and writable:
  - `<runtime-root>/PLENS`
  - `<runtime-root>/INPUT`
  - `<runtime-root>/KFIELD`
- Python environment with required packages.
- `compute_pp_plot_data.slurm` and `compute_pt_plot_data.slurm` present.

## One-Command Submission

Use:

```bash
scripts/submit_thesis_cache_pipeline.sh \
  --runtime-root /path/to/your/runtime-root \
  --venv-activate /path/to/your/venv/bin/activate \
  --pipeline both
```

What it submits:

1. PP noiseless seed (`mv_lensed`)
2. PP noiseless scenario array (`mv_input_kappa`, `mv_internal_qest`, `tt_internal_polqest`)
3. PP noisy seed (`mv_lensed`)
4. PP noisy scenario array (same 3 scenarios)
5. PP validation stage
6. PP `wf_eff` stage after noisy+noiseless arrays finish
7. PT noiseless seed + array
8. PT noisy seed + array

## Dry Run

Preview commands only:

```bash
scripts/submit_thesis_cache_pipeline.sh \
  --runtime-root /path/to/your/runtime-root \
  --venv-activate /path/to/your/venv/bin/activate \
  --pipeline both \
  --dry-run
```

## Tuning Runtime Requests

Defaults:
- PP: `--time-pp 3-00:00:00`, `--mem-pp 12G`
- PT: `--time-pt 1-00:00:00`, `--mem-pt 8G`
- Partition: `regularmedium`

Override example:

```bash
scripts/submit_thesis_cache_pipeline.sh \
  --runtime-root /path/to/your/runtime-root \
  --venv-activate /path/to/your/venv/bin/activate \
  --pipeline pp \
  --partition regularlong \
  --time-pp 5-00:00:00 \
  --mem-pp 16G
```

## Re-run Behavior

- Cache builders skip existing outputs by default.
- For forced rebuilds, submit direct jobs with `FORCE=1` via the slurm wrappers.
- Avoid running duplicate jobs for the same stage/scenario at the same time.

## PR4 Hybrid Amplitude Test

For a fast PR3-vs-PR4 amplitude comparison, use a separate PR4 runtime root and a
separate output cache directory. The supported fast path is a hybrid test:

- data-side inputs come from the PR4 runtime
- simulation-side `PLENS` products are reused from the PR3 runtime
- amplitude-fit metadata and histogram samples are reused from the PR3 cache

This is useful for checking whether the PR3 data-point amplitudes are stable under a
PR4 data-map replacement, especially for the noisy Pol-QE point. It is not a fully
self-consistent PR4 Monte Carlo analysis.

Typical pieces:

- PR3 runtime root: `<runtime-root-pr3>`
- PR4 runtime root: `<runtime-root-pr4>`
- PR3 amplitude cache: `<repo-root>/THESIS/cache/amplitude_results`
- PR4 test cache: `<repo-root>/THESIS/cache/amplitude_results_pr4test`

Submission pattern:

```bash
sbatch   --export=ALL,VENV_ACTIVATE=/path/to/your/venv/bin/activate,REPO_ROOT=/path/to/your/repo,RUNTIME_ROOT=<runtime-root-pr4>,REFERENCE_RUNTIME_ROOT=<runtime-root-pr3>,STAGE=kde_noisy_dataonly,OUTPUT_DIR=/path/to/your/repo/THESIS/cache/amplitude_results_pr4test,REFERENCE_CACHE_DIR=/path/to/your/repo/THESIS/cache/amplitude_results,FORCE=1   /path/to/your/repo/compute_amplitude_plot_data.slurm
```

Required reference file in the PR3 cache dir:

- `noisy_amplitude_fitmeta_agr2.npz`

Build it once with:

```bash
sbatch   --export=ALL,VENV_ACTIVATE=/path/to/your/venv/bin/activate,REPO_ROOT=/path/to/your/repo,RUNTIME_ROOT=<runtime-root-pr3>,STAGE=fitmeta_noisy,OUTPUT_DIR=/path/to/your/repo/THESIS/cache/amplitude_results,FORCE=1   /path/to/your/repo/compute_amplitude_plot_data.slurm
```

