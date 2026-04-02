# Pipeline Refactor Plan (Performance + Reliability)

## Goals
- Keep scientific outputs unchanged relative to the current thesis-reproduction baseline.
- Reduce wall-clock runtime by parallelizing safely.
- Make reruns idempotent and predictable.
- Eliminate hidden expensive work in notebooks.

## Current Pain Points
- Expensive lazy computation is triggered from cache-building calls.
- Scenario runs are coupled through shared baseline caches.
- Partial cache artifacts cause file-collision failures.
- Corrupted/truncated FITS files are discovered late.
- Notebook execution depends on fragile kernel/session state.

## Stage Model (Target Architecture)
1. `stage-baseline`
- Build baseline lensed products that are shared by other scenarios.
- Outputs: baseline `ivfs`, `qlms`, mean-field caches.

2. `stage-scenario`
- Build scenario-specific products (`mv_input_kappa`, `mv_internal_qest`, `tt_internal_polqest`, etc.).
- Keep writes confined to scenario-local trees.

3. `stage-bandpower`
- Compute per-scenario bandpower/statistics products only.
- No simulation remapping or mean-field generation allowed here.

4. `stage-cache`
- Create compact `THESIS/cache/*.npz` outputs for figures.
- Pure aggregation/serialization only.

5. `stage-plot`
- Notebook or script plotting from cache only.
- No expensive physics work.

## Parallelization Strategy
- Parallelize scenario jobs only when they do not write into shared cache trees.
- Parallelize within a scenario by simulation chunks for heavy loops:
  - Example chunking: `60-89`, `90-119`, ... , `270-299`.
- Merge chunk outputs in a deterministic reducer step.
- Run `wf_eff` only after all required scenario outputs are complete.

## Reliability Rules
- Each stage must support `skip-existing` behavior by default.
- Use atomic writes for final artifacts (`tmp -> rename`).
- Add preflight checks for corrupted raw FITS and suspiciously small cache products.
- Never overwrite scenario caches implicitly; require explicit clean/reset flags.

## Data Upgrade Path (PR4)
- Keep PR4 migration as a separate branch after refactor baseline is stable.
- Validate PR4 outputs against current baseline stage-by-stage.
- Do not mix PR4 upgrade with refactor logic changes in the same commits.

## Immediate Next Steps
1. Add cache/raw-file audit tooling (done in `scripts/audit_delensing_cache.py`).
2. Split expensive cache builders into explicit stages and chunk runners.
3. Add stage-level Slurm wrappers with dependency chaining.
4. Enforce plotting-from-cache-only in notebooks/scripts.
