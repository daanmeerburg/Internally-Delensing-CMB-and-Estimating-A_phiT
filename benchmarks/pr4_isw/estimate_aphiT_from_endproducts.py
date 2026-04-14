#!/usr/bin/env python3
"""Measure A_phiT from external PR4 kappa end products using the current pipeline.

This uses the existing clean-delensing machinery with kPhi="input", which reads
external kappa alms from the directory pointed to by $KFIELD.

The result is directly comparable to this repo's own KDE-based amplitude plots,
but it is not the official PR4 likelihood benchmark.
"""

import argparse
import importlib
import os
import sys
from pathlib import Path

import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--parfile-module",
        default="parfiles.Noise.parfile",
        help="Parfile module to use for the T-map side of the cross-correlation.",
    )
    p.add_argument(
        "--fitmeta",
        default="/home3/p283342/Delensing/clean-delensing/THESIS/cache/amplitude_results/noisy_amplitude_fitmeta_agr2.npz",
        help="Cached fit metadata produced by compute_amplitude_plot_data.py --stage fitmeta_noisy.",
    )
    p.add_argument(
        "--hist-cache",
        default="/home3/p283342/Delensing/clean-delensing/THESIS/cache/amplitude_results/noisy_amplitude_hist_agr2.npz",
        help="Optional noisy histogram cache used to report the reference PR3 simulation distribution.",
    )
    p.add_argument("--mc-start", type=int, default=60)
    p.add_argument("--mc-stop", type=int, default=300, help="Exclusive upper bound.")
    p.add_argument(
        "--with-pr4-sims",
        action="store_true",
        help="Also evaluate the external-input amplitude on the PR4 simulation set exposed through KFIELD.",
    )
    p.add_argument("--label", default="PR4 input-kappa benchmark")
    p.add_argument("--output", default=None, help="Optional .npz output path.")
    return p.parse_args()


def fit_amplitude(cl_data, c_fid, sigma, ls):
    seg = sigma[ls].copy()
    seg[seg == 0] = np.finfo(float).eps
    weights = 1.0 / seg**2
    denom = float(np.sum((c_fid[ls] ** 2) * weights))
    amp = float(np.sum(cl_data[ls] * c_fid[ls] * weights) / denom)
    return amp, weights, denom


def load_fitmeta(path):
    z = np.load(path, allow_pickle=True)
    labels = [str(x) for x in z["labels"]]
    return {
        "labels": labels,
        "ls": z["ls"],
        "c_fid": z["c_fid"],
        "lmax": int(z["lmax"]),
        "w": {
            labels[0]: z["w0"],
            labels[1]: z["w1"],
            labels[2]: z["w2"],
        },
        "den": {
            labels[0]: float(z["den0"]),
            labels[1]: float(z["den1"]),
            labels[2]: float(z["den2"]),
        },
    }


def fit_from_cached_weights(cl_data, fitmeta, label):
    ls = fitmeta["ls"]
    c_fid = fitmeta["c_fid"]
    w_arr = fitmeta["w"][label]
    denom = fitmeta["den"][label]
    amp = float(np.sum(cl_data[ls] * c_fid[ls] * w_arr) / denom)
    sigma = float(np.sqrt(1.0 / denom))
    return amp, sigma


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    kfield = os.environ.get("KFIELD")
    if not kfield:
        raise EnvironmentError("KFIELD is not set.")
    kfield_path = Path(kfield)
    data_klm = kfield_path / "klm_-01.fits"
    if not data_klm.exists():
        raise FileNotFoundError(f"Missing data kappa file: {data_klm}")

    parfile = importlib.import_module(args.parfile_module)

    fitmeta = load_fitmeta(Path(args.fitmeta).expanduser().resolve())
    label_mv = fitmeta["labels"][0]
    lmax = int(fitmeta["lmax"])
    ls = fitmeta["ls"]

    cl_data = parfile.qcls_pt.get_sim_qcl("input", -1, lmax=lmax).copy()
    a_data, a_sig = fit_from_cached_weights(cl_data, fitmeta, label_mv)

    sim_idxs = np.arange(args.mc_start, args.mc_stop)
    a_sims = None
    a_mean = None
    a_std = None
    if args.with_pr4_sims:
        a_sims = np.zeros(sim_idxs.size)
        for ii, idx in enumerate(sim_idxs):
            cl_sim = parfile.qcls_pt.get_sim_qcl("input", int(idx), lmax=lmax).copy()
            a_sims[ii], _ = fit_from_cached_weights(cl_sim, fitmeta, label_mv)
        a_mean = float(a_sims.mean())
        a_std = float(a_sims.std(ddof=1))

    ref_hist = Path(args.hist_cache).expanduser().resolve()
    ref_mean = None
    ref_std = None
    if ref_hist.exists():
        zh = np.load(ref_hist, allow_pickle=True)
        ref_mean = float(zh["mean0"])
        ref_std = float(zh["std0"])

    print(f"label:          {args.label}")
    print(f"parfile:        {args.parfile_module}")
    print(f"KFIELD:         {kfield_path}")
    print(f"data kappa:     {data_klm}")
    print(f"fit range:      L={ls[0]}..{ls[-1]}")
    print(f"A_data:         {a_data:.6f}")
    print(f"sigma_fit:      {a_sig:.6f}")
    if args.with_pr4_sims:
        print(f"MC sims:        {sim_idxs[0]}..{sim_idxs[-1]}")
        print(f"A_sims mean:    {a_mean:.6f}")
        print(f"A_sims std:     {a_std:.6f}")
    if ref_mean is not None:
        print(f"PR3 hist mean:  {ref_mean:.6f}")
        print(f"PR3 hist std:   {ref_std:.6f}")

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            out,
            label=args.label,
            parfile=args.parfile_module,
            kfield=str(kfield_path),
            lmin=int(ls[0]),
            lmax=int(ls[-1]),
            ell=ls,
            c_fid=fitmeta["c_fid"],
            cl_data=cl_data,
            a_data=float(a_data),
            a_sigma=float(a_sig),
            a_sims=a_sims,
            a_mean=a_mean,
            a_std=a_std,
            ref_mean=ref_mean,
            ref_std=ref_std,
            mc_sims=sim_idxs if args.with_pr4_sims else np.array([], dtype=int),
        )
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
