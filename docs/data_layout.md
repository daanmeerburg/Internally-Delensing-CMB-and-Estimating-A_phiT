# Data Layout

## Runtime Paths

The project uses four main path variables:

- `PLENS`: output root for cached estimators, spectra, and intermediate products
- `INPUT`: CMB, noise, and SMICA map inputs
- `PARAMS`: mask and dCl adjustment files
- `KFIELD`: input lensing maps used for delensed simulations

## Expected Files

### `INPUT`

```text
<INPUT>/cmb_00000.fits
<INPUT>/cmb_00001.fits
...
<INPUT>/noise_00000.fits
<INPUT>/noise_00001.fits
...
<INPUT>/SMICA.fits
```

### `KFIELD`

```text
<KFIELD>/klm_000.fits
<KFIELD>/klm_001.fits
...
```

### `PARAMS`

```text
<PARAMS>/mask.fits.gz
<PARAMS>/dcl_sim
<PARAMS>/dcl_dat
```

## Suggested Scratch Layout

For the current cluster setup, a clean layout under
`/scratch/hb-CosmoGroup/Delensing` is:

```text
/scratch/hb-CosmoGroup/Delensing/
  CMB/sims/raw/
  Noise/sims/raw/
  SMICA/mission/raw/
  Lensing/input/raw/
  INPUT/
  KFIELD/
```

Where:

- the product-specific directories keep raw archive filenames
- `INPUT/` contains symlinks named exactly as the pipeline expects
- `KFIELD/` contains `klm_%03d.fits` symlinks or files

## Relationship To Repository Helpers

The repository expects the runtime directories in this layout to exist before
notebook cache builders are run.

After the simulation products are available, the repository helper scripts:

- `compute_pt_plot_data.py`
- `compute_pp_plot_data.py`
- `run_single_scenario.py`

can be used together with their Slurm wrappers to generate notebook-ready cache
products without modifying the raw input layout.
