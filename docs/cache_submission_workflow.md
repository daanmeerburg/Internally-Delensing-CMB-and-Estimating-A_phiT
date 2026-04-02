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
