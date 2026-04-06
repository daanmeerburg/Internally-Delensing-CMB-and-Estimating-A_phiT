#!/usr/bin/env python3
"""Quick sanity check that a kappa map has non-zero low-L C_ell^{phi T}.

Usage example:
  /home3/p283342/delens-env/bin/python scripts/check_phiT_signal.py \
    --klm /scratch/hb-CosmoGroup/PR4_Lensing/PR4_klm_dat_p.fits \
    --tmap /scratch/hb-CosmoGroup/Delensing/INPUT/SMICA.fits
"""

import argparse
from pathlib import Path
import numpy as np
import healpy as hp


def alm_trim(alm: np.ndarray, lmax_in: int, lmax_out: int) -> np.ndarray:
    """Trim healpy alm array to a lower lmax."""
    if lmax_out >= lmax_in:
        return alm
    out = np.zeros(hp.Alm.getsize(lmax_out), dtype=alm.dtype)
    for m in range(lmax_out + 1):
        for l in range(m, lmax_out + 1):
            out[hp.Alm.getidx(lmax_out, l, m)] = alm[hp.Alm.getidx(lmax_in, l, m)]
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--klm", required=True, help="Path to kappa alm FITS (e.g. PR4_klm_dat_p.fits)")
    p.add_argument("--tmap", required=True, help="Path to temperature map FITS (field 0)")
    p.add_argument("--tfield", type=int, default=0, help="FITS field index to treat as T (default: 0)")
    p.add_argument("--lmax", type=int, default=None, help="Optional lmax cap")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    klm_path = Path(args.klm)
    tmap_path = Path(args.tmap)
    if not klm_path.exists():
        raise FileNotFoundError(f"Missing klm file: {klm_path}")
    if not tmap_path.exists():
        raise FileNotFoundError(f"Missing tmap file: {tmap_path}")

    klm = hp.read_alm(str(klm_path))
    lmax_in = hp.Alm.getlmax(len(klm))
    lmax_k = lmax_in
    if args.lmax is not None:
        lmax_k = min(lmax_k, int(args.lmax))
    klm = alm_trim(klm, lmax_in=lmax_in, lmax_out=lmax_k)

    ell = np.arange(lmax_k + 1, dtype=float)
    fac = np.zeros_like(ell)
    fac[1:] = 2.0 / (ell[1:] * (ell[1:] + 1.0))
    plm = hp.almxfl(klm, fac)

    t = hp.read_map(str(tmap_path), field=int(args.tfield), dtype=np.float64, verbose=False)
    tlm = hp.map2alm(t, lmax=lmax_k, pol=False, iter=0)

    cl_pt = hp.alm2cl(plm, tlm)

    print(f"klm:  {klm_path}")
    print(f"tmap: {tmap_path}")
    print(f"T field: {int(args.tfield)}")
    print(f"lmax used: {lmax_k}")
    for lo, hi in [(2, 20), (21, 40), (41, 80), (2, 80)]:
        seg = cl_pt[lo : hi + 1]
        print(
            f"L={lo:>2}-{hi:<3} sum={np.sum(seg): .6e} mean={np.mean(seg): .6e} median={np.median(seg): .6e}"
        )
    print("cl_pt[2:12] =", np.array2string(cl_pt[2:12], precision=3, suppress_small=False))


if __name__ == "__main__":
    main()
