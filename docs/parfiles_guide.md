# Parfiles Guide

## What A Parfile Does

A parfile is the configuration module that defines one full analysis setup. It
selects:

- which simulations are used
- whether instrumental noise is present
- whether delensing is applied
- which estimator libraries are built
- filtering, masking, and response configuration

The driver script imports parfiles as Python modules and passes them directly
into the downstream pipeline code.

## High-Level Split

### `parfiles/noNoise/`

Configurations without instrumental noise in the simulated maps.

Typical use:

- idealized reference runs
- isolating delensing effects without added noise complications

### `parfiles/Noise/`

Configurations with Planck-like noise included.

Typical use:

- realistic pipeline runs
- reproducing the main thesis-style analysis conditions

## Main Variants

### `parfile.py`

Baseline lensed setup for a given noise scenario.

Thesis role:

- reference lensed comparison
- used as the baseline "MV: lensed" case in the main `phi-T` and `phi-phi`
  comparison plots

### `parfile_delensed.py`

Delensed setup using the input lensing field from `KFIELD`.

Thesis role:

- "delensed with input `\kappa_{LM}`"
- isolates the effect of ideal delensing with access to the simulation truth
- used as the direct-input-delensed comparison branch in the notebooks

### `parfile_delensed_qest.py`

Delensed setup focused on a specific quadratic-estimator configuration.

Thesis role:

- "internally delensed with MV-QEST"
- uses a reconstructed lensing field rather than the input truth map
- this is the main internal-delensing branch used for the thesis-style MV
  comparisons

### `parfile_delensed_PolQEST.py`

Delensed setup using the polarization-related estimator branch.

Thesis role:

- "internally delensed with Pol-QEST" in the current notebooks
- used as the alternative delensing branch compared against the MV-QEST case

## Thesis Scenario Matrix

The current notebooks use the same conceptual four-way comparison in both the
`Noise/` and `noNoise/` branches:

1. lensed baseline
2. delensed with input `kappa`
3. internally delensed with MV-QEST
4. internally delensed with Pol-QEST

That mapping to code is:

- `parfiles/noNoise/parfile.py`
  baseline noiseless lensed
- `parfiles/noNoise/parfile_delensed.py`
  noiseless delensed with input `kappa`
- `parfiles/noNoise/parfile_delensed_qest.py`
  noiseless internally delensed with MV-QEST
- `parfiles/noNoise/parfile_delensed_PolQEST.py`
  noiseless internally delensed with Pol-QEST
- `parfiles/Noise/parfile.py`
  noisy lensed baseline
- `parfiles/Noise/parfile_delensed.py`
  noisy delensed with input `kappa`
- `parfiles/Noise/parfile_delensed_qest.py`
  noisy internally delensed with MV-QEST
- `parfiles/Noise/parfile_delensed_PolQEST.py`
  noisy internally delensed with Pol-QEST

## Estimator Keys

The current driver uses estimator strings such as:

- `p`
- `p_p`
- `ptt`

In the current code and notebooks they are used as follows:

### `p`

This is the main estimator key used for the baseline MV-style lensing
reconstruction and for the MV-internal-delensing comparisons.

Current usage:

- baseline lensed comparisons in `PT_results.ipynb` and `PP_results.ipynb`
- input-`kappa` delensed comparisons
- internally delensed MV-QEST comparisons

### `p_p`

This key appears in the baseline polarization-QE branch and in some `phi-phi`
comparisons. It is not the main default key for the thesis `phi-T` scenario
plots, but it is part of the broader estimator set used by the code.

### `ptt`

This key is used for the Pol-QEST-delensed comparison branch in the current
notebooks.

Current usage:

- "internally delensed with Pol-QEST" comparison in both noisy and noiseless
  `phi-T` and `phi-phi` plots

## Practical Pairing Rules

The current thesis-style pairings are:

- `parfile.py` with `p`
- `parfile.py` with `p_p` for the extra baseline polarization-QE branch
- `parfile_delensed.py` with `p`
- `parfile_delensed_qest.py` with `p`
- `parfile_delensed_PolQEST.py` with `ptt`

## Data Dependencies

Most parfiles depend on:

- `PLENS` for generated intermediate products
- `INPUT` for CMB/noise/data maps
- `PARAMS` for masks and dCl inputs
- `KFIELD` for input lensing maps in delensed cases

## Remaining Gap

One thing is still not fully explicit from the code alone:

- the low-level mathematical definition of each estimator key inside the
  underlying `plancklens` conventions

For now, the safe interpretation is the operational one above: which parfile
uses which key and which thesis comparison it corresponds to.
