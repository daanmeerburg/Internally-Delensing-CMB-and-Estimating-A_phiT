# PR4 ISW Benchmark

This folder separates two different tasks that should not be conflated.

1. Official PR4 benchmark
Use the packaged likelihood tables from the official `planck_PR4_lensing`
repository to recover the published ISW-lensing benchmark numbers.

2. Current-pipeline end-product test
Use the public PR4 `klm` end products inside this repo's existing pipeline to
measure an `A_{\phi T}` amplitude that can be compared against the KDE
distributions already built from the PR3 simulation pipeline.

These are not the same object.

## Files

- `benchmark_official_pt.py`
  - Reads the official PR4 likelihood tables from a local checkout of
    `carronj/planck_PR4_lensing`.
  - Reports the table-level PT-only amplitude together with the published paper
    benchmark values.
  - This is the clean reference for "what does the official PR4 analysis say?".

- `setup_kfield_pr4.sh`
  - Creates a `KFIELD` adapter directory from the public PR4 lensing products.
  - Exposes the data map as `klm_-01.fits`, which matches the current pipeline's
    `idx = -1` data convention.
  - Exposes simulation maps as `klm_060.fits`, `klm_061.fits`, ...

- `estimate_aphiT_from_endproducts.py`
  - Uses the current `clean-delensing` pipeline with `kPhi="input"` to measure
    an amplitude from the external PR4 `klm` products.
  - This is the bridge to your current notebook/KDE workflow.
  - It is not the official PR4 likelihood.

## Typical workflow

1. Check the official benchmark:

```bash
python benchmarks/pr4_isw/benchmark_official_pt.py \
  --likelihood-root /tmp/planck_PR4_lensing
```

2. Build a `KFIELD` adapter for the public PR4 MV map:

```bash
benchmarks/pr4_isw/setup_kfield_pr4.sh \
  --variant pr4 \
  --dest /scratch/hb-CosmoGroup/KFIELD_PR4_MV
```

3. Run the current pipeline with the PR4 end products:

```bash
export KFIELD=/scratch/hb-CosmoGroup/KFIELD_PR4_MV
export INPUT=/scratch/hb-CosmoGroup/Delensing_PR4test/INPUT
export PLENS=/scratch/hb-CosmoGroup/Delensing_PR4test/PLENS
export PARAMS=/home3/p283342/Delensing/clean-delensing/input

/home3/p283342/delens-env/bin/python \
  benchmarks/pr4_isw/estimate_aphiT_from_endproducts.py \
  --parfile-module parfiles.Noise.parfile \
  --output THESIS/cache/amplitude_results_pr4test/noisy_aphiT_input_pr4_mv.npz
```

4. Validate external temperature delensing with the PR4 tracer:

```bash
export INPUT=/scratch/hb-CosmoGroup/Delensing_PR4test/INPUT
export PLENS=/scratch/hb-CosmoGroup/Delensing_PR4ext/PLENS
export KFIELD=/scratch/hb-CosmoGroup/KFIELD_PR4_MV
export PARAMS=/home3/p283342/Delensing/clean-delensing/input

/home3/p283342/delens-env/bin/python \
  benchmarks/pr4_isw/validate_external_delensing.py
```

## Interpretation

- If `benchmark_official_pt.py` and the paper agree, the official reference is
  under control.
- If `estimate_aphiT_from_endproducts.py` differs, the remaining mismatch is in
  this repo's filtering, masking, weighting, or amplitude definition, not in the
  PR4 public `klm` products themselves.
