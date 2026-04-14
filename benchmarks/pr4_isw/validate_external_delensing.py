#!/usr/bin/env python3
"""Generate and compare lensed vs externally-delensed data T alms.

This is a data-only validation run for the existing external-delensing path.
It uses:
  - `parfiles.Noise.parfile` for the lensed data-side filtered T alm
  - `parfiles.Noise.parfile_delensed` for the externally-delensed filtered T alm

The runtime is controlled by the environment:
  - INPUT
  - PLENS
  - KFIELD
  - PARAMS

Recommended setup for a PR4 external-tracer test:
  INPUT  -> /scratch/.../Delensing_PR4test/INPUT
  PLENS  -> /scratch/.../Delensing_PR4ext/PLENS
  KFIELD -> /scratch/.../KFIELD_PR4_MV
"""

import argparse
import importlib
import sys
from pathlib import Path

import healpy as hp
import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--lensed-parfile",
        default="parfiles.Noise.parfile",
        help="Module used for the lensed filtered data T alm.",
    )
    p.add_argument(
        "--delensed-parfile",
        default="parfiles.Noise.parfile_delensed",
        help="Module used for the externally-delensed filtered data T alm.",
    )
    p.add_argument("--lmax", type=int, default=2048)
    p.add_argument(
        "--output",
        default="/home3/p283342/Delensing/clean-delensing/THESIS/cache/amplitude_results_pr4test/pr4_external_delensing_validation.npz",
        help="Output .npz path.",
    )
    return p.parse_args()


def main():
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    par_lensed = importlib.import_module(args.lensed_parfile)
    par_delensed = importlib.import_module(args.delensed_parfile)

    print("Loading lensed filtered data T alm...")
    tlm_lensed = par_lensed.ivfs.get_sim_tmliklm(-1)
    print("Loading externally-delensed filtered data T alm...")
    tlm_delensed = par_delensed.ivfs.get_sim_tmliklm(-1)

    lmax = int(args.lmax)
    cl_lensed = hp.alm2cl(tlm_lensed, lmax_out=lmax)
    cl_delensed = hp.alm2cl(tlm_delensed, lmax_out=lmax)
    ell = np.arange(lmax + 1)

    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.zeros_like(cl_lensed)
        mask = cl_lensed != 0
        frac[mask] = 1.0 - cl_delensed[mask] / cl_lensed[mask]

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out,
        ell=ell,
        cl_lensed=cl_lensed,
        cl_delensed=cl_delensed,
        frac_reduction=frac,
        lensed_parfile=args.lensed_parfile,
        delensed_parfile=args.delensed_parfile,
    )

    print(f"Wrote {out}")
    print(f"lensed dat_tlm:   {Path(par_lensed.ivfs.lib_dir) / 'dat_tlm.fits'}")
    print(f"delensed dat_tlm: {Path(par_delensed.ivfs.lib_dir) / 'dat_tlm.fits'}")
    print(f"Mean frac reduction L=30..300: {np.mean(frac[30:301]):.6e}")


if __name__ == "__main__":
    main()
