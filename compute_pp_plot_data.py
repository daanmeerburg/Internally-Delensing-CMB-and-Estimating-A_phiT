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


SCENARIO_SLUGS = ("mv_lensed", "mv_input_kappa", "mv_internal_qest", "tt_internal_polqest")


def load_scenarios(load_noiseless: bool, load_noisy: bool):
    ctx = {}
    if load_noiseless:
        import parfiles.noNoise.parfile as par_nn
        import parfiles.noNoise.parfile_delensed as par_nn_del
        import parfiles.noNoise.parfile_delensed_qest as par_nn_qest
        import parfiles.noNoise.parfile_delensed_PolQEST as par_nn_polq

        ctx["noiseless"] = [
            (par_nn, "MV: lensed", "p", "mv_lensed"),
            (par_nn_del, r"MV: delensed with input $\kappa_{LM}$", "p", "mv_input_kappa"),
            (par_nn_qest, "MV: internally delensed with MV-QEST", "p", "mv_internal_qest"),
            (par_nn_polq, "TT: internally delensed with Pol-QEST", "ptt", "tt_internal_polqest"),
        ]
        ctx["par_nn"] = par_nn
        ctx["par_nn_polq"] = par_nn_polq
    if load_noisy:
        import parfiles.Noise.parfile as par_n
        import parfiles.Noise.parfile_delensed as par_n_del
        import parfiles.Noise.parfile_delensed_qest as par_n_qest
        import parfiles.Noise.parfile_delensed_PolQEST as par_n_polq

        ctx["noisy"] = [
            (par_n, "MV: lensed", "p", "mv_lensed"),
            (par_n_del, r"MV: delensed with input $\kappa_{LM}$", "p", "mv_input_kappa"),
            (par_n_qest, "MV: internally delensed with MV-QEST", "p", "mv_internal_qest"),
            (par_n_polq, "TT: internally delensed with Pol-QEST", "ptt", "tt_internal_polqest"),
        ]
        ctx["par_n"] = par_n
        ctx["par_n_polq"] = par_n_polq
    return ctx


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
            f"Valid slugs: {', '.join(SCENARIO_SLUGS)}"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where cached .npz files will be written.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing cache files instead of skipping them.",
    )
    return parser.parse_args()


def validation_target(output_dir: Path) -> Path:
    return output_dir / "validation_noiseless_agr2.npz"


def clpp_targets(output_dir: Path, group: str, bin_type: str, scenario_slug: str | None = None):
    fid = output_dir / f"{group}_clpp_fiducial_{bin_type}.npz"
    if scenario_slug is not None:
        return [fid, output_dir / f"{group}_clpp_{scenario_slug}_{bin_type}.npz"]
    return [fid] + [output_dir / f"{group}_clpp_{slug}_{bin_type}.npz" for slug in SCENARIO_SLUGS]


def wf_targets(output_dir: Path):
    return [
        output_dir / "noiseless_wf_vs_eff_fullA_10.npz",
        output_dir / "noisy_wf_vs_eff_fullA_10.npz",
    ]


def needs_work(paths, force: bool) -> bool:
    if force:
        return True
    return not all(path.exists() for path in paths)


def save_validation(output_dir: Path, par_nn, force: bool = False) -> None:
    from binner_sims import binner_sims

    target = output_dir / "validation_noiseless_agr2.npz"
    if target.exists() and not force:
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
    force: bool = False,
) -> None:
    from binner_sims import binner_sims

    fid_target = output_dir / f"{name}_clpp_fiducial_{bin_type}.npz"
    ell = None
    fid = None
    calib = None
    if fid_target.exists() and not force:
        print(f"Using existing {fid_target}")
        cached = np.load(fid_target, allow_pickle=True)
        ell = cached["ell"]
        fid = cached["fid"]
        if "calib" in cached and cached["calib"].size > 0:
            calib = cached["calib"]
    else:
        base_par = scenarios[0][0]
        base_est = scenarios[0][2]
        base = binner_sims(base_est, base_est, base_par, bin_type)
        ell = base.bin_lavs
        fid = base.fid_bandpowers

        if name == "noisy":
            sims_raw = base.get_sims_bandpowers() - base.get_mcn0() - base.get_n1()
            calib = fid / sims_raw

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
        if target.exists() and not force:
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


def save_efficiency_cases(output_dir: Path, par_nn, par_nn_polq, par_n, par_n_polq, force: bool = False) -> None:
    from binner_sims import binner_sims

    cases = {
        "noiseless": (par_nn, par_nn_polq),
        "noisy": (par_n, par_n_polq),
    }
    for name, (par_base, par_del) in cases.items():
        target = output_dir / f"{name}_wf_vs_eff_fullA_10.npz"
        if target.exists() and not force:
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

    run_validation = args.stage in ("all", "validation") and needs_work([validation_target(output_dir)], args.force)
    run_clpp_noiseless = args.stage in ("all", "clpp_noiseless") and needs_work(
        clpp_targets(output_dir, "noiseless", "fullA_20", args.scenario), args.force
    )
    run_clpp_noisy = args.stage in ("all", "clpp_noisy") and needs_work(
        clpp_targets(output_dir, "noisy", "fullA_20", args.scenario), args.force
    )
    run_wf = args.stage in ("all", "wf_eff") and needs_work(wf_targets(output_dir), args.force)

    if args.stage in ("all", "validation") and not run_validation:
        print(f"Skipping existing {validation_target(output_dir)}")
    if args.stage in ("all", "clpp_noiseless") and not run_clpp_noiseless:
        for p in clpp_targets(output_dir, "noiseless", "fullA_20", args.scenario):
            print(f"Skipping existing {p}")
    if args.stage in ("all", "clpp_noisy") and not run_clpp_noisy:
        for p in clpp_targets(output_dir, "noisy", "fullA_20", args.scenario):
            print(f"Skipping existing {p}")
    if args.stage in ("all", "wf_eff") and not run_wf:
        for p in wf_targets(output_dir):
            print(f"Skipping existing {p}")

    if not (run_validation or run_clpp_noiseless or run_clpp_noisy or run_wf):
        print("All requested PP cache targets already exist; nothing to do.")
        return

    ctx = load_scenarios(
        load_noiseless=(run_validation or run_clpp_noiseless or run_wf),
        load_noisy=(run_clpp_noisy or run_wf),
    )

    if run_validation:
        save_validation(output_dir, ctx["par_nn"], force=args.force)
    if run_clpp_noiseless:
        save_clpp_group("noiseless", ctx["noiseless"], "fullA_20", output_dir, args.scenario, force=args.force)
    if run_clpp_noisy:
        save_clpp_group("noisy", ctx["noisy"], "fullA_20", output_dir, args.scenario, force=args.force)
    if run_wf:
        save_efficiency_cases(output_dir, ctx["par_nn"], ctx["par_nn_polq"], ctx["par_n"], ctx["par_n_polq"], force=args.force)


if __name__ == "__main__":
    main()
