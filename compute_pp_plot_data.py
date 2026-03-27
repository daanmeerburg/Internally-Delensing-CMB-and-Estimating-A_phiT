#!/usr/bin/env python3
"""
Compute cached phi-phi plot inputs for the thesis notebooks.

This script writes compact .npz products for the main PP thesis figures so the
notebook can focus on plotting rather than recomputing simulation statistics.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import parfiles.noNoise.parfile as par_nn
import parfiles.noNoise.parfile_delensed as par_nn_del
import parfiles.noNoise.parfile_delensed_qest as par_nn_qest
import parfiles.noNoise.parfile_delensed_PolQEST as par_nn_polq
import parfiles.Noise.parfile as par_n
import parfiles.Noise.parfile_delensed as par_n_del
import parfiles.Noise.parfile_delensed_qest as par_n_qest
import parfiles.Noise.parfile_delensed_PolQEST as par_n_polq
from binner_sims import binner_sims


NOISELESS = [
    (par_nn, "MV: lensed", "p", "mv_lensed"),
    (par_nn_del, r"MV: delensed with input $\kappa_{LM}$", "p", "mv_input_kappa"),
    (par_nn_qest, "MV: internally delensed with MV-QEST", "p", "mv_internal_qest"),
    (par_nn_polq, "TT: internally delensed with Pol-QEST", "ptt", "tt_internal_polqest"),
]

NOISY = [
    (par_n, "MV: lensed", "p", "mv_lensed"),
    (par_n_del, r"MV: delensed with input $\kappa_{LM}$", "p", "mv_input_kappa"),
    (par_n_qest, "MV: internally delensed with MV-QEST", "p", "mv_internal_qest"),
    (par_n_polq, "TT: internally delensed with Pol-QEST", "ptt", "tt_internal_polqest"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("all", "validation", "clpp_noiseless", "clpp_noisy", "wf_eff"),
        default="all",
        help="Which PP cache stage to compute.",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help=(
            "Optional scenario slug for clpp stages. "
            "Valid slugs: mv_lensed, mv_input_kappa, mv_internal_qest, tt_internal_polqest"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where cached .npz files will be written.",
    )
    return parser.parse_args()


def save_validation(output_dir: Path) -> None:
    target = output_dir / "validation_noiseless_agr2.npz"
    if target.exists():
        print(f"Skipping existing {target}")
        return
    b0 = binner_sims("p", "p", par_nn, "agr2")
    ell = b0.bin_lavs
    fid = b0.fid_bandpowers
    sims = b0.get_sims_bandpowers() - b0.get_mcn0() - b0.get_n1()
    np.savez(target, ell=ell, fid=fid, sims=sims, nsims=240, bin_type="agr2")
    print(f"Wrote {target}")


def save_clpp_group(
    name: str,
    scenarios,
    bin_type: str,
    output_dir: Path,
    scenario_slug: str | None = None,
) -> None:
    base_par = scenarios[0][0]
    base_est = scenarios[0][2]
    base = binner_sims(base_est, base_est, base_par, bin_type)
    ell = base.bin_lavs
    fid = base.fid_bandpowers

    calib = None
    if name == "noisy":
        sims_raw = base.get_sims_bandpowers() - base.get_mcn0() - base.get_n1()
        calib = fid / sims_raw

    fid_target = output_dir / f"{name}_clpp_fiducial_{bin_type}.npz"
    if fid_target.exists():
        print(f"Skipping existing {fid_target}")
    else:
        np.savez(
            fid_target,
            ell=ell,
            fid=fid,
            calib=calib if calib is not None else np.array([]),
            bin_type=bin_type,
            group=name,
        )
        print(f"Wrote {fid_target}")

    valid_slugs = {slug for _, _, _, slug in scenarios}
    if scenario_slug is not None and scenario_slug not in valid_slugs:
        raise ValueError(f"Unknown scenario slug {scenario_slug!r} for {name}. Valid: {sorted(valid_slugs)}")

    for parfile, label, estimator, slug in scenarios:
        if scenario_slug is not None and slug != scenario_slug:
            continue
        target = output_dir / f"{name}_clpp_{slug}_{bin_type}.npz"
        if target.exists():
            print(f"Skipping existing {target}")
            continue

        print(f"Computing {name} clpp: {label} [{estimator}] from {parfile.TEMP}")
        b = binner_sims(estimator, estimator, parfile, bin_type)
        bp_mean, bp_err = b.get_sims_bandpowers_with_error()
        bp_mean = bp_mean - (b.get_mcn0() + b.get_n1())
        if calib is not None:
            bp_mean = bp_mean * calib
            bp_err = bp_err * calib

        np.savez(
            target,
            ell=ell,
            bp_mean=bp_mean,
            bp_err=bp_err,
            label=label,
            estimator=estimator,
            temp=parfile.TEMP,
            bin_type=bin_type,
            group=name,
            slug=slug,
        )
        print(f"Wrote {target}")


def save_efficiency_cases(output_dir: Path) -> None:
    cases = {
        "noiseless": (par_nn, par_nn_polq),
        "noisy": (par_n, par_n_polq),
    }
    for name, (par_base, par_del) in cases.items():
        target = output_dir / f"{name}_wf_vs_eff_fullA_10.npz"
        if target.exists():
            print(f"Skipping existing {target}")
            continue

        bw = binner_sims("p_p", "p_p", par_base, "fullA_10")
        ell_w = np.arange(len(bw.get_WF()))
        w = bw.get_WF()

        bl = binner_sims("p", "p", par_base, "fullA_10")
        ell = bl.bin_lavs
        c_len, c_len_err = bl.get_sims_bandpowers_with_error()
        c_len = c_len - bl.get_mcn0() - bl.get_n1()

        bd = binner_sims("ptt", "ptt", par_del, "fullA_10")
        c_del, c_del_err = bd.get_sims_bandpowers_with_error()
        c_del = c_del - bd.get_mcn0() - bd.get_n1()

        eff_mean = 1.0 - (c_del / c_len)
        eff_err = np.sqrt((c_del_err / c_len) ** 2 + (c_del * c_len_err / c_len ** 2) ** 2)

        np.savez(
            target,
            ell=ell,
            ell_w=ell_w,
            w=w,
            eff_mean=eff_mean,
            eff_err=eff_err,
            bin_type="fullA_10",
            group=name,
        )
        print(f"Wrote {target}")


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir) if args.output_dir else repo_root / "THESIS" / "cache" / "pp_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.stage in ("all", "validation"):
        save_validation(output_dir)
    if args.stage in ("all", "clpp_noiseless"):
        save_clpp_group("noiseless", NOISELESS, "fullA_20", output_dir, args.scenario)
    if args.stage in ("all", "clpp_noisy"):
        save_clpp_group("noisy", NOISY, "fullA_20", output_dir, args.scenario)
    if args.stage in ("all", "wf_eff"):
        save_efficiency_cases(output_dir)


if __name__ == "__main__":
    main()
