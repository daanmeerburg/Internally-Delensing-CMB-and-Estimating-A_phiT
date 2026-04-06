#!/usr/bin/env python3
"""Mean-field diagnostics for phi-T null tests.

This script probes whether the small non-zero null-test offsets are consistent
with finite/shared mean-field subtraction effects by recomputing null amplitudes
with multiple MF simulation sets.
"""

import argparse
from pathlib import Path

import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--group",
        choices=("noiseless", "noisy", "both"),
        default="noiseless",
        help="Which scenario group to test.",
    )
    p.add_argument(
        "--bin-type",
        default="agr2",
        help="Binner type for null-test amplitude fit.",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for diagnostic .npz",
    )
    p.add_argument(
        "--eval-start",
        type=int,
        default=60,
        help="First simulation index for null-test evaluation set.",
    )
    p.add_argument(
        "--eval-stop",
        type=int,
        default=300,
        help="Stop simulation index (exclusive) for null-test evaluation set.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing diagnostic .npz output.",
    )
    return p.parse_args()


def load_scenarios(group):
    if group in ("noiseless", "both"):
        import parfiles.noNoise.parfile as par_nn
        import parfiles.noNoise.parfile_delensed_qest as par_nn_qest
        import parfiles.noNoise.parfile_delensed_PolQEST as par_nn_polq

        noiseless = [
            (par_nn, "MV: lensed", "p"),
            (par_nn_qest, "MV: internally delensed with MV-QEST", "p"),
            (par_nn_polq, "TT: internally delensed with Pol-QEST", "ptt"),
        ]
    else:
        noiseless = []

    if group in ("noisy", "both"):
        import parfiles.Noise.parfile as par_n
        import parfiles.Noise.parfile_delensed_qest as par_n_qest
        import parfiles.Noise.parfile_delensed_PolQEST as par_n_polq

        noisy = [
            (par_n, "MV: lensed", "p"),
            (par_n_qest, "MV: internally delensed with MV-QEST", "p"),
            (par_n_polq, "TT: internally delensed with Pol-QEST", "ptt"),
        ]
    else:
        noisy = []

    return noiseless, noisy


def fit_amplitude(cl_arr, sigma_arr, c_fid, ls):
    seg = sigma_arr[ls].copy()
    seg[seg == 0] = np.finfo(float).eps
    w = 1.0 / seg**2
    den = np.sum((c_fid[ls] ** 2) * w)
    num = np.sum(cl_arr[ls] * c_fid[ls] * w)
    a = num / den if den > 0 else np.nan
    sa = np.sqrt(1.0 / den) if den > 0 else np.nan
    return float(a), float(sa)


def main():
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    out_dir = (
        Path(args.output_dir)
        if args.output_dir
        else repo_root / "THESIS" / "cache" / "amplitude_results"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fiducial amplitude-fit setup
    from binner_sims import ffp10_binner_phiT
    import parfiles.noNoise.parfile as par_nn

    b0 = ffp10_binner_phiT("p", par_nn, args.bin_type)
    c_fid = b0.clpt_fid.copy()
    ls = np.arange(3, 101)

    eval_sims = np.arange(args.eval_start, args.eval_stop, dtype=int)
    if eval_sims.size == 0:
        raise ValueError("Evaluation simulation set is empty.")

    # Candidate MF sets
    mf_sets = {
        "disjoint30_a": np.arange(0, 30, dtype=int),
        "disjoint30_b": np.arange(30, 60, dtype=int),
        "disjoint60": np.arange(0, 60, dtype=int),
        "overlap60": np.arange(60, 120, dtype=int),
        "mixed120": np.arange(0, 120, dtype=int),
    }

    noiseless, noisy = load_scenarios(args.group)
    groups = []
    if noiseless:
        groups.append(("noiseless", noiseless))
    if noisy:
        groups.append(("noisy", noisy))

    if not groups:
        raise ValueError("No scenarios selected.")

    labels = []
    rows = []

    for group_name, scenarios in groups:
        for parfile, label, kphi in scenarios:
            if label not in labels:
                labels.append(label)

            b = ffp10_binner_phiT(kphi, parfile, args.bin_type)
            # Ensure we only use null-test branch
            qlib = parfile.qcls_pt_ss

            # Save original state so we can restore after diagnostics.
            orig_mf = np.array(qlib.mc_sims_mf, copy=True)
            orig_MF_cache = qlib.MF

            for mf_name, mf_sims in mf_sets.items():
                qlib.mc_sims_mf = np.array(mf_sims, copy=True)
                qlib.MF = None  # force re-fetch/rebuild MF for this set

                cl_bar, cl_err = b.get_cL_PHI_T_with_error(
                    mc_sims=eval_sims,
                    binned=False,
                    scaled=False,
                    cross_maps=True,
                )
                a, sa = fit_amplitude(cl_bar, cl_err, c_fid, ls)

                rows.append(
                    (
                        group_name,
                        label,
                        kphi,
                        mf_name,
                        int(mf_sims.size),
                        float(a),
                        float(sa),
                        float(a / sa) if sa > 0 else np.nan,
                    )
                )

            # restore original
            qlib.mc_sims_mf = orig_mf
            qlib.MF = orig_MF_cache

    dtype = [
        ("group", "U16"),
        ("label", "U96"),
        ("kphi", "U8"),
        ("mf_name", "U24"),
        ("mf_count", "i4"),
        ("A_null", "f8"),
        ("sigma_A", "f8"),
        ("z", "f8"),
    ]
    arr = np.array(rows, dtype=dtype)

    out = out_dir / f"nulltest_mf_diagnostics_{args.group}_{args.bin_type}.npz"
    if out.exists() and not args.force:
        print(f"Exists, not overwriting: {out}")
    else:
        np.savez(
            out,
            results=arr,
            eval_sims=eval_sims,
            fit_ls=ls,
            labels=np.array(labels, dtype=object),
        )
        print(f"Wrote {out}")
    print("\nSummary:")
    for r in arr:
        print(
            f"{r['group']:9s} | {r['label'][:44]:44s} | {r['mf_name']:11s} "
            f"| A={r['A_null']:+.5f} +/- {r['sigma_A']:.5f} | z={r['z']:+.2f}"
        )


if __name__ == "__main__":
    main()
