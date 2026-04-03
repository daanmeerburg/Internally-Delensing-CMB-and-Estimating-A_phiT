# Upstream Parallel Workflow (Scenario-Level)

This workflow parallelizes the heavy upstream stages for one scenario by
splitting simulation ranges and chaining Slurm dependencies.

Stages:
1. `qlms` as an array over bias simulation chunks
2. `mf` as a single dependency job
3. `qcls` as an array over variance simulation chunks
4. `phi_t` as a final dependency job

## New Script

Use:

```bash
scripts/submit_upstream_parallel_scenario.sh \
  --scenario 5 \
  --runtime-root /path/to/your/runtime-root \
  --venv-activate /path/to/your/venv/bin/activate \
  --bias-total 60 \
  --var-total 240
```

Notes:
- `--scenario` index follows `run_single_scenario.py` scenario list.
- `--bias-total` and `--var-total` are explicit to avoid heavy metadata import.
- Adjust `--bias-chunk` and `--var-chunk` for parallelism vs. queue pressure.

## Dry Run First

```bash
scripts/submit_upstream_parallel_scenario.sh \
  --scenario 5 \
  --runtime-root /path/to/your/runtime-root \
  --venv-activate /path/to/your/venv/bin/activate \
  --bias-total 60 \
  --var-total 240 \
  --dry-run
```

## Practical Chunk Defaults

- Conservative:
  - `--bias-chunk 30 --var-chunk 60` (2 qlms tasks, 4 qcls tasks)
- More parallel:
  - `--bias-chunk 15 --var-chunk 30` (4 qlms tasks, 8 qcls tasks)

Use conservative values first if the file system is sensitive to many concurrent
writers.

## Advanced: Run Single Stage Manually

`run_single_scenario.py` now supports:
- `--stage all|qlms|mf|qcls|phi_t`
- `--bias-start`, `--bias-count`
- `--var-start`, `--var-count`

Manual examples:

```bash
python run_single_scenario.py --scenario 5 --stage qlms --bias-start 120 --bias-count 30 --skip-phi-t
python run_single_scenario.py --scenario 5 --stage mf --skip-phi-t
python run_single_scenario.py --scenario 5 --stage qcls --var-start 180 --var-count 60 --skip-phi-t
python run_single_scenario.py --scenario 5 --stage phi_t --var-start 60 --var-count 240
```
