#!/usr/bin/env python3
"""Profile A_phiT using the official PR4 ISW-lensing likelihood code.

This script uses the official `planck_PR4_lensing` repository directly and
profiles the `ISWLensingTT` likelihood as a function of a multiplicative
amplitude applied to the fiducial `C_L^{\phi T}` spectrum.

It therefore targets the benchmark object used in the official PR4 paper more
closely than a naive fit to the packaged PT block.

Requirements:
  - `cobaya`
  - `camb`
  - local checkout of `carronj/planck_PR4_lensing`

Note:
  The current public repo needs a small local patch in
  `planckpr4lensing/iswlens_jtliks/lik.py` so that `_cls2dls` supports the
  `'TE'` key as well as `'ET'`.
"""

import argparse
import sys
from copy import deepcopy
from pathlib import Path

from scipy.optimize import minimize_scalar


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--likelihood-root",
        default="/tmp/planck_PR4_lensing",
        help="Local checkout of the official planck_PR4_lensing repository.",
    )
    p.add_argument("--amin", type=float, default=0.0)
    p.add_argument("--amax", type=float, default=2.0)
    p.add_argument("--curvature-step", type=float, default=1e-3)
    return p.parse_args()


def main():
    args = parse_args()
    root = Path(args.likelihood_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from planckpr4lensing.planckpr4iswlensing import ISWLensingTT
    from planckpr4lensing.iswlens_jtliks import lik as likmod

    lik = ISWLensingTT(info={}, packages_path=None, initialize=False)
    lik.initialize()
    cls_fid = deepcopy(likmod.CLS_FID)

    def chi2(amp):
        cls = deepcopy(cls_fid)
        cls["pt"] *= amp
        return float(lik.mylik.get_chi2_tt_pt_mtt(cls))

    res = minimize_scalar(chi2, bounds=(args.amin, args.amax), method="bounded")
    ahat = float(res.x)
    chi2min = float(res.fun)

    h = float(args.curvature_step)
    second = (chi2(ahat + h) - 2.0 * chi2min + chi2(ahat - h)) / (h * h)
    sigma = (2.0 / second) ** 0.5

    print(f"likelihood root: {root}")
    print(f"Ahat:            {ahat:.6f}")
    print(f"sigma:           {sigma:.6f}")
    print(f"chi2_min:        {chi2min:.6f}")
    print("published PR4:   1.01 +/- 0.25")


if __name__ == "__main__":
    main()
