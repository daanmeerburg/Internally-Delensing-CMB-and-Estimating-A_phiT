# Pipeline Overview

## Goal

The project measures how internal delensing changes the lensing-temperature
cross-correlation and related lensing observables in Planck FFP10 simulations.
The thesis frames this in terms of reducing the ISW-lensing induced bias on
primordial non-Gaussianity constraints.

## Main Inputs

- Simulated CMB maps: `cmb_%05d.fits`
- Simulated noise maps: `noise_%05d.fits`
- Data map: `SMICA.fits`
- Input lensing maps: `klm_%03d.fits`
- Mask and dCl files from `input/`

## Main Driver

The current pipeline is orchestrated by `run_parfiles.py`. Its top-level loop
iterates over a list of parameter-file modules and estimator choices.

For each `(parfile, estimator)` pair it does four broad steps:

1. Build simulated quadratic lensing maps (QLMs).
2. Build the mean-field QLM used for subtraction.
3. Build quadratic cross/auto spectra (QCLs) for the variance simulations.
4. Bin the resulting `C_L^{\phi T}` spectrum.

## Step 1: Scenario Definition Through Parfiles

The parfile modules define the analysis scenario:

- noisy vs no-noise
- lensed vs internally delensed
- estimator choice
- simulation libraries
- filtering and response settings

The `Noise/` and `noNoise/` directories correspond to whether instrumental
noise is included in the simulated sky maps.

## Step 2: Simulation And Filtering Setup

Inside each parfile the code sets:

- harmonic limits such as `lmax_ivf` and `lmax_qlm`
- beam and pixel window transfer functions
- fiducial unlensed and lensed spectra
- masks
- inverse-variance filtered libraries (`ivfs`)

For delensed cases, the parfile also uses the input lensing maps from `KFIELD`
to produce delensed simulations.

## Step 3: QLM Generation

`run_parfiles.py` calls `par.qlms_dd.get_sim_qlm(estimator, i)` over the bias
simulation set. This constructs the quadratic lensing estimator output for each
simulation realization.

Meaning:

- `qlm` is the harmonic-space reconstruction of the lensing field
- `dd` denotes the main data-data style estimator library used in the pipeline

## Step 4: Mean-Field Estimation

`run_parfiles.py` then calls:

```python
par.qlms_dd.get_sim_qlm_mf(estimator, par.mc_sims_mf_dd)
```

This computes the estimator mean field that is later subtracted from the raw
lensing reconstruction. This is needed because masking, anisotropic filtering,
and other analysis details produce a non-zero average reconstruction even when
no cosmological signal should be present.

## Step 5: QCL Generation

The code loops over `mc_sims_var` and builds:

- `qcls_ss`: simulation-simulation spectra used for variance and bias handling
- `qcls_dd`: main reconstruction spectra

These cached libraries are later used to derive the Wiener filter and response
corrections.

## Step 6: Phi-T Cross Spectrum

The `qecl_pt.library_phiT` class computes the cross-spectrum between:

- the reconstructed or input lensing field `phi`
- the temperature map `T`

Core operations:

1. load or build the reconstructed `phi`
2. subtract the mean field when using reconstructed `phi`
3. load the matching temperature harmonic coefficients
4. compute the cross-spectrum with `healpy.alm2cl`
5. divide by `fsky`
6. cache the result

## Step 7: Response Correction And Binning

`ffp10_binner_phiT` in `binner_sims.py` takes the raw `phi-T` spectrum and:

1. applies the lensing-response correction
2. optionally applies a Wiener filter
3. bins the spectrum with Planck-style weights

This is the stage that turns raw simulation outputs into the bandpowers used in
the final plots and amplitude estimates.

## Thesis Link

This code path corresponds most directly to the thesis sections discussing:

- CMB lensing reconstruction
- ISW-lensing correlations
- internal delensing
- the `C_L^{\phi T}` and `A_{\phi T}` summary statistics

In the clean fork, each pipeline stage should be annotated with references to
the relevant thesis chapter or equation numbers.
