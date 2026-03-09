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

## Relationship To The Downloader

The standalone downloader script at:

`/home3/p283342/Delensing/download_planck_data.sh`

was written to populate this layout directly for the CMB and noise simulation
sets and to support configurable SMICA and lensing URLs.
