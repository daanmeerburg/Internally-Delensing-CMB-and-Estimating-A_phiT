#!/usr/bin/env python3
"""Read the official PR4 likelihood tables and report PT-only amplitudes.

This script does not rebuild the PR4 likelihood machinery. It reads the stored
bandpower amplitudes and covariance blocks from a local checkout of the
official `carronj/planck_PR4_lensing` repository and performs the minimal
PT-only scalar-amplitude fit

    A = (1^T C^-1 d) / (1^T C^-1 1)

on the PT block.

This table-level fit is useful as a reproducible reference. The published paper
numbers are also printed explicitly because the exact paper benchmark includes
the official likelihood construction, not just this plain PT-only fit.
"""

import argparse
from pathlib import Path

import numpy as np


DATASETS = {
    "pr4": "planckpr4lensing/data_pr4/iswliks/jtlik_data_lmax99_PR4_July25",
    "pr3commander": "planckpr4lensing/data_pr4/iswliks/jtlik_data_lmax99_PR3commander",
}

PUBLISHED = {
    "pr4": (1.01, 0.25),
    "pr3maps": (0.94, 0.30),
}


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--likelihood-root",
        default="/tmp/planck_PR4_lensing",
        help="Local checkout of the official planck_PR4_lensing repository.",
    )
    p.add_argument(
        "--dataset",
        choices=tuple(DATASETS),
        default="pr4",
        help="Which packaged table set to analyse.",
    )
    return p.parse_args()


def load_table(root, dataset):
    base = root / DATASETS[dataset]
    meas = np.loadtxt(base / "meas.txt")
    cov = np.loadtxt(base / "cov.txt")
    return meas, cov


def infer_pt_block(meas, cov, dataset):
    if dataset == "pr4":
        # The packaged PR4 table stores TT, PT, PP as 98 + 98 + 98 amplitudes.
        ntt = 98
        npt = 98
    elif dataset == "pr3commander":
        # The packaged PR3 commander reference stores TT and PT only.
        ntt = 98
        npt = meas.shape[0] - ntt
    else:
        raise ValueError(dataset)

    pt = meas[ntt:ntt + npt]
    cpt = cov[ntt:ntt + npt, ntt:ntt + npt]
    return pt, cpt


def fit_scalar_amplitude(pt, cov):
    ones = np.ones(pt.size)
    cov_inv = np.linalg.inv(cov)
    norm = float(ones @ cov_inv @ ones)
    amp = float(ones @ cov_inv @ pt / norm)
    sig = float(norm ** -0.5)
    return amp, sig


def main() -> None:
    args = parse_args()
    root = Path(args.likelihood_root).expanduser().resolve()
    meas, cov = load_table(root, args.dataset)
    pt, cpt = infer_pt_block(meas, cov, args.dataset)
    amp, sig = fit_scalar_amplitude(pt, cpt)

    print(f"likelihood root: {root}")
    print(f"dataset:         {args.dataset}")
    print(f"PT points:       {pt.size}")
    print(f"table-level PT-only amplitude: {amp:.6f} +/- {sig:.6f}")
    print()
    print("Published PR4 paper benchmarks:")
    print(f"  PR4 maps: {PUBLISHED['pr4'][0]:.2f} +/- {PUBLISHED['pr4'][1]:.2f}")
    print(f"  PR3 maps: {PUBLISHED['pr3maps'][0]:.2f} +/- {PUBLISHED['pr3maps'][1]:.2f}")
    print()
    print("Note:")
    print("  The table-level PT-only fit above is a useful reproducibility check,")
    print("  but the published benchmark is defined by the official likelihood")
    print("  construction in the PR4 analysis, not only by this simple block fit.")


if __name__ == "__main__":
    main()
