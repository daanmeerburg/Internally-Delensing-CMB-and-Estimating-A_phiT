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

### `parfile_delensed.py`

Delensed setup using the input lensing field from `KFIELD`.

### `parfile_delensed_qest.py`

Delensed setup focused on a specific quadratic-estimator configuration.

### `parfile_delensed_PolQEST.py`

Delensed setup using the polarization-related estimator branch.

## Estimator Keys Seen In The Driver

The current driver uses estimator strings such as:

- `p`
- `p_p`
- `ptt`

These should be documented explicitly in the clean fork because the meaning is
not obvious from the names alone. At minimum the docs should state:

- what field is being reconstructed
- whether the estimator is minimum-variance, temperature-only, or another form
- which thesis plots used each estimator

## Data Dependencies

Most parfiles depend on:

- `PLENS` for generated intermediate products
- `INPUT` for CMB/noise/data maps
- `PARAMS` for masks and dCl inputs
- `KFIELD` for input lensing maps in delensed cases

## Documentation Gap To Close

The most important missing documentation is not syntax, but meaning:

- why a given parfile exists
- what scientific comparison it supports
- what output directory it writes to
- what estimator key should be paired with it
