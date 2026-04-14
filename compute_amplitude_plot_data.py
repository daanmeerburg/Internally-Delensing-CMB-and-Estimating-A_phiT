#!/usr/bin/env python3
"""Compute cached amplitude plot inputs for THESIS/Amplitude.ipynb.

This script moves heavy simulation aggregation off the notebook path.
"""

import argparse
from pathlib import Path

import numpy as np


LABELS = (
    "MV: lensed",
    "MV: internally delensed with MV-QEST",
    "TT: internally delensed with Pol-QEST",
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--stage",
        choices=("all", "hist", "fitmeta_noisy", "kde_noisy", "kde_noisy_dataonly", "nulltest"),
        default="all",
        help="Which amplitude cache stage to compute.",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Directory where cached .npz files will be written.",
    )
    p.add_argument(
        "--reference-cache-dir",
        default=None,
        help="Optional directory to load existing amplitude caches/metadata from.",
    )
    p.add_argument("--force", action="store_true", help="Overwrite existing cache files.")
    return p.parse_args()


def load_parfiles():
    import parfiles.noNoise.parfile as par_nn
    import parfiles.noNoise.parfile_delensed_qest as par_nn_qest
    import parfiles.noNoise.parfile_delensed_PolQEST as par_nn_polq
    import parfiles.Noise.parfile as par_n
    import parfiles.Noise.parfile_delensed_qest as par_n_qest
    import parfiles.Noise.parfile_delensed_PolQEST as par_n_polq

    noiseless = [
        (par_nn, "MV: lensed", "p"),
        (par_nn_qest, "MV: internally delensed with MV-QEST", "p"),
        (par_nn_polq, "TT: internally delensed with Pol-QEST", "ptt"),
    ]
    noisy = [
        (par_n, "MV: lensed", "p"),
        (par_n_qest, "MV: internally delensed with MV-QEST", "p"),
        (par_n_polq, "TT: internally delensed with Pol-QEST", "ptt"),
    ]
    return noiseless, noisy


def get_common_fid(bin_type: str, lmin: int, lmax_fit: int):
    from binner_sims import ffp10_binner_phiT
    import parfiles.noNoise.parfile as par_nn

    b0 = ffp10_binner_phiT("p", par_nn, bin_type)
    lmax = b0.lmax
    c_fid = b0.clpt_fid.copy()
    ls = np.arange(lmin, lmax_fit + 1)
    return lmax, c_fid, ls


def compute_hist_data(noiseless, noisy, sim_idxs, bin_type, lmin=3, lmax_fit=100):
    from binner_sims import ffp10_binner_phiT
    from plancklens.utils import cli

    lmax, c_fid, ls = get_common_fid(bin_type, lmin, lmax_fit)
    fid_sq = c_fid[ls] ** 2

    sigma = {"noiseless": {}, "noisy": {}}
    cl_sim = {"noiseless": {}, "noisy": {}}

    for group, scenarios in (("noiseless", noiseless), ("noisy", noisy)):
        for parfile, label, kphi in scenarios:
            b = ffp10_binner_phiT(kphi, parfile, bin_type)
            _, sig = b.get_cL_PHI_T_with_error(mc_sims=sim_idxs, binned=False, scaled=False)
            sigma[group][label] = sig

            arr = np.zeros((sim_idxs.size, lmax + 1))
            resp = cli(parfile.qresp_dd.get_response(kphi, "p")[: lmax + 1])
            for ii, idx in enumerate(sim_idxs):
                cl = parfile.qcls_pt.get_sim_qcl(kphi, idx, lmax=lmax).copy()
                cl *= resp
                arr[ii] = cl
            cl_sim[group][label] = arr

    w = {"noiseless": {}, "noisy": {}}
    den = {"noiseless": {}, "noisy": {}}
    a_vals = {"noiseless": {}, "noisy": {}}
    means = {"noiseless": {}, "noisy": {}}
    stds = {"noiseless": {}, "noisy": {}}

    for group in ("noiseless", "noisy"):
        for label in sigma[group]:
            seg = sigma[group][label][ls].copy()
            seg[seg == 0] = np.finfo(float).eps
            w_arr = 1.0 / seg**2
            d = np.sum(fid_sq * w_arr)
            w[group][label] = w_arr
            den[group][label] = d

            sims = cl_sim[group][label]
            a = np.array([np.sum(row[ls] * c_fid[ls] * w_arr) / d for row in sims])
            a_vals[group][label] = a
            means[group][label] = float(a.mean())
            stds[group][label] = float(a.std(ddof=1))

    return {
        "lmax": lmax,
        "ls": ls,
        "c_fid": c_fid,
        "a_vals": a_vals,
        "means": means,
        "stds": stds,
        "w": w,
        "den": den,
    }


def compute_fit_meta(scenarios, sim_idxs, bin_type, lmin=3, lmax_fit=100):
    from binner_sims import ffp10_binner_phiT

    lmax, c_fid, ls = get_common_fid(bin_type, lmin, lmax_fit)
    fid_sq = c_fid[ls] ** 2

    sigma = {}
    w = {}
    den = {}

    for parfile, label, kphi in scenarios:
        b = ffp10_binner_phiT(kphi, parfile, bin_type)
        _, sig = b.get_cL_PHI_T_with_error(mc_sims=sim_idxs, binned=False, scaled=False)
        sigma[label] = sig

        seg = sig[ls].copy()
        seg[seg == 0] = np.finfo(float).eps
        w_arr = 1.0 / seg**2
        w[label] = w_arr
        den[label] = float(np.sum(fid_sq * w_arr))

    return {
        "labels": list(LABELS),
        "lmax": int(lmax),
        "ls": ls,
        "c_fid": c_fid,
        "w": w,
        "den": den,
        "bin_type": bin_type,
    }


def save_hist_npz(data, out_dir: Path):
    for group in ("noiseless", "noisy"):
        path = out_dir / f"{group}_amplitude_hist_agr2.npz"
        np.savez(
            path,
            labels=np.array(LABELS, dtype=object),
            a0=data["a_vals"][group][LABELS[0]],
            a1=data["a_vals"][group][LABELS[1]],
            a2=data["a_vals"][group][LABELS[2]],
            mean0=data["means"][group][LABELS[0]],
            mean1=data["means"][group][LABELS[1]],
            mean2=data["means"][group][LABELS[2]],
            std0=data["stds"][group][LABELS[0]],
            std1=data["stds"][group][LABELS[1]],
            std2=data["stds"][group][LABELS[2]],
            lmin=int(data["ls"][0]),
            lmax=int(data["ls"][-1]),
            bin_type="agr2",
        )
        print(f"Wrote {path}")


def save_fit_meta_npz(meta, out_dir: Path):
    path = out_dir / "noisy_amplitude_fitmeta_agr2.npz"
    np.savez(
        path,
        labels=np.array(meta["labels"], dtype=object),
        ls=meta["ls"],
        c_fid=meta["c_fid"],
        lmax=int(meta["lmax"]),
        w0=meta["w"][LABELS[0]],
        w1=meta["w"][LABELS[1]],
        w2=meta["w"][LABELS[2]],
        den0=float(meta["den"][LABELS[0]]),
        den1=float(meta["den"][LABELS[1]]),
        den2=float(meta["den"][LABELS[2]]),
        bin_type=meta["bin_type"],
    )
    print(f"Wrote {path}")


def save_noisy_kde_npz(data, noisy, out_dir: Path):
    from plancklens.utils import cli

    lmax = int(data["lmax"])
    a_data = {}
    for parfile, label, kphi in noisy:
        cl_data = parfile.qcls_pt.get_sim_qcl(kphi, -1, lmax=lmax).copy()
        resp = cli(parfile.qresp_dd.get_response(kphi, "p")[: lmax + 1])
        cl_data *= resp
        w_arr = data["w"]["noisy"][label]
        d = data["den"]["noisy"][label]
        ls = data["ls"]
        c_fid = data["c_fid"]
        a_data[label] = float(np.sum(cl_data[ls] * c_fid[ls] * w_arr) / d)

    path = out_dir / "noisy_amplitude_kde_agr2.npz"
    np.savez(
        path,
        labels=np.array(LABELS, dtype=object),
        a0=data["a_vals"]["noisy"][LABELS[0]],
        a1=data["a_vals"]["noisy"][LABELS[1]],
        a2=data["a_vals"]["noisy"][LABELS[2]],
        adata0=a_data[LABELS[0]],
        adata1=a_data[LABELS[1]],
        adata2=a_data[LABELS[2]],
        bin_type="agr2",
    )
    print(f"Wrote {path}")


def load_fit_meta_npz(path: Path):
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
        "bin_type": str(z["bin_type"]),
    }


def compute_noisy_data_amplitudes(noisy, fit_meta):
    from plancklens.utils import cli

    lmax = int(fit_meta["lmax"])
    ls = fit_meta["ls"]
    c_fid = fit_meta["c_fid"]
    a_data = {}

    for parfile, label, kphi in noisy:
        cl_data = parfile.qcls_pt.get_sim_qcl(kphi, -1, lmax=lmax).copy()
        resp = cli(parfile.qresp_dd.get_response(kphi, "p")[: lmax + 1])
        cl_data *= resp
        w_arr = fit_meta["w"][label]
        d = fit_meta["den"][label]
        a_data[label] = float(np.sum(cl_data[ls] * c_fid[ls] * w_arr) / d)

    return a_data


def save_noisy_kde_from_hist_and_data(hist_path: Path, a_data, out_dir: Path):
    hist = np.load(hist_path, allow_pickle=True)
    path = out_dir / "noisy_amplitude_kde_agr2.npz"
    np.savez(
        path,
        labels=hist["labels"],
        a0=hist["a0"],
        a1=hist["a1"],
        a2=hist["a2"],
        adata0=a_data[LABELS[0]],
        adata1=a_data[LABELS[1]],
        adata2=a_data[LABELS[2]],
        bin_type=hist["bin_type"],
    )
    print(f"Wrote {path}")


def save_nulltest_npz(noiseless, noisy, sim_idxs, bin_type, out_dir: Path):
    from binner_sims import ffp10_binner_phiT

    _, c_fid, ls = get_common_fid(bin_type, 3, 100)
    fid_sq = c_fid[ls] ** 2

    null_cl = {"noiseless": {}, "noisy": {}}
    null_err = {"noiseless": {}, "noisy": {}}

    for group, scenarios in (("noiseless", noiseless), ("noisy", noisy)):
        for parfile, label, kphi in scenarios:
            b = ffp10_binner_phiT(kphi, parfile, bin_type)
            cl_bar, cl_err = b.get_cL_PHI_T_with_error(
                mc_sims=sim_idxs,
                binned=False,
                scaled=False,
                cross_maps=True,
            )
            null_cl[group][label] = cl_bar
            null_err[group][label] = cl_err

    def fit(cl_arr, sig_arr):
        seg = sig_arr[ls].copy()
        seg[seg == 0] = np.finfo(float).eps
        w = 1.0 / seg**2
        den = np.sum(fid_sq * w)
        num = np.sum(cl_arr[ls] * c_fid[ls] * w)
        return float(num / den), float(np.sqrt(1.0 / den))

    out = {}
    for group in ("noiseless", "noisy"):
        for label in LABELS:
            out[(group, label)] = fit(null_cl[group][label], null_err[group][label])

    path = out_dir / "amplitude_nulltest_agr2.npz"
    np.savez(
        path,
        labels=np.array(LABELS, dtype=object),
        a_noiseless_0=out[("noiseless", LABELS[0])][0],
        a_noiseless_1=out[("noiseless", LABELS[1])][0],
        a_noiseless_2=out[("noiseless", LABELS[2])][0],
        sa_noiseless_0=out[("noiseless", LABELS[0])][1],
        sa_noiseless_1=out[("noiseless", LABELS[1])][1],
        sa_noiseless_2=out[("noiseless", LABELS[2])][1],
        a_noisy_0=out[("noisy", LABELS[0])][0],
        a_noisy_1=out[("noisy", LABELS[1])][0],
        a_noisy_2=out[("noisy", LABELS[2])][0],
        sa_noisy_0=out[("noisy", LABELS[0])][1],
        sa_noisy_1=out[("noisy", LABELS[1])][1],
        sa_noisy_2=out[("noisy", LABELS[2])][1],
        bin_type="agr2",
    )
    print(f"Wrote {path}")


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    out_dir = Path(args.output_dir) if args.output_dir else repo_root / "THESIS" / "cache" / "amplitude_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    ref_dir = Path(args.reference_cache_dir) if args.reference_cache_dir else out_dir

    targets = {
        "hist": [out_dir / "noiseless_amplitude_hist_agr2.npz", out_dir / "noisy_amplitude_hist_agr2.npz"],
        "fitmeta_noisy": [out_dir / "noisy_amplitude_fitmeta_agr2.npz"],
        "kde_noisy": [out_dir / "noisy_amplitude_kde_agr2.npz"],
        "kde_noisy_dataonly": [out_dir / "noisy_amplitude_kde_agr2.npz"],
        "nulltest": [out_dir / "amplitude_nulltest_agr2.npz"],
    }

    noiseless, noisy = load_parfiles()
    sim_idxs = np.arange(60, 300)
    bin_type = "agr2"

    data = None

    def need(stage: str) -> bool:
        if args.force:
            return True
        return not all(p.exists() for p in targets[stage])

    if args.stage in ("all", "hist") and need("hist"):
        data = compute_hist_data(noiseless, noisy, sim_idxs, bin_type)
        save_hist_npz(data, out_dir)
    elif args.stage in ("all", "hist"):
        for p in targets["hist"]:
            print(f"Skipping existing {p}")

    if args.stage in ("all", "fitmeta_noisy") and need("fitmeta_noisy"):
        meta = compute_fit_meta(noisy, sim_idxs, bin_type)
        save_fit_meta_npz(meta, out_dir)
    elif args.stage in ("all", "fitmeta_noisy"):
        for p in targets["fitmeta_noisy"]:
            print(f"Skipping existing {p}")

    if args.stage in ("all", "kde_noisy") and need("kde_noisy"):
        if data is None:
            data = compute_hist_data(noiseless, noisy, sim_idxs, bin_type)
        save_noisy_kde_npz(data, noisy, out_dir)
    elif args.stage in ("all", "kde_noisy"):
        for p in targets["kde_noisy"]:
            print(f"Skipping existing {p}")

    if args.stage == "kde_noisy_dataonly" and need("kde_noisy_dataonly"):
        fitmeta_path = ref_dir / "noisy_amplitude_fitmeta_agr2.npz"
        hist_path = ref_dir / "noisy_amplitude_hist_agr2.npz"
        if not fitmeta_path.exists():
            raise FileNotFoundError(
                f"Missing fit metadata cache: {fitmeta_path}. "
                "Run --stage fitmeta_noisy once in the reference cache directory first."
            )
        if not hist_path.exists():
            raise FileNotFoundError(
                f"Missing noisy histogram cache: {hist_path}. "
                "Run --stage hist once in the reference cache directory first."
            )
        fit_meta = load_fit_meta_npz(fitmeta_path)
        a_data = compute_noisy_data_amplitudes(noisy, fit_meta)
        save_noisy_kde_from_hist_and_data(hist_path, a_data, out_dir)
    elif args.stage == "kde_noisy_dataonly":
        for p in targets["kde_noisy_dataonly"]:
            print(f"Skipping existing {p}")

    if args.stage in ("all", "nulltest") and need("nulltest"):
        save_nulltest_npz(noiseless, noisy, sim_idxs, bin_type, out_dir)
    elif args.stage in ("all", "nulltest"):
        for p in targets["nulltest"]:
            print(f"Skipping existing {p}")


if __name__ == "__main__":
    main()
