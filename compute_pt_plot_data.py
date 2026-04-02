#!/usr/bin/env python3
"""
Compute cached phi-T plot inputs for the thesis notebooks.

This moves the expensive simulation aggregation out of the notebook and writes
compact .npz files that the notebook can load quickly.

Examples:
    python compute_pt_plot_data.py --group noiseless
    python compute_pt_plot_data.py --group noisy
    python compute_pt_plot_data.py --group both --bin-type fullA_10
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


SCENARIO_SLUGS = ("mv_lensed", "mv_input_kappa", "mv_internal_qest", "tt_internal_polqest")


def load_scenarios():
    import parfiles.noNoise.parfile as par_nn
    import parfiles.noNoise.parfile_delensed as par_nn_del
    import parfiles.noNoise.parfile_delensed_qest as par_nn_qest
    import parfiles.noNoise.parfile_delensed_PolQEST as par_nn_polq
    import parfiles.Noise.parfile as par_n
    import parfiles.Noise.parfile_delensed as par_n_del
    import parfiles.Noise.parfile_delensed_qest as par_n_qest
    import parfiles.Noise.parfile_delensed_PolQEST as par_n_polq

    noiseless = [
        (par_nn, "MV: lensed", "p", "mv_lensed"),
        (par_nn_del, r"MV: delensed with input $\kappa_{LM}$", "p", "mv_input_kappa"),
        (par_nn_qest, "MV: int. delensed with MV-QEST", "p", "mv_internal_qest"),
        (par_nn_polq, "TT: int. delensed with Pol-QEST", "ptt", "tt_internal_polqest"),
    ]
    noisy = [
        (par_n, "MV: lensed", "p", "mv_lensed"),
        (par_n_del, r"MV: delensed with input $\kappa_{LM}$", "p", "mv_input_kappa"),
        (par_n_qest, "MV: int. delensed with MV-QEST", "p", "mv_internal_qest"),
        (par_n_polq, "TT: int. delensed with Pol-QEST", "ptt", "tt_internal_polqest"),
    ]
    return {"noiseless": noiseless, "noisy": noisy}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--group",
        choices=("noiseless", "noisy", "both"),
        default="both",
        help="Which scenario group to compute.",
    )
    parser.add_argument(
        "--bin-type",
        default="fullA_10",
        help="Binning scheme passed into ffp10_binner_phiT.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory where cached .npz files will be written.",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help=(
            "Optional scenario slug to compute inside the chosen group(s). "
            f"Valid slugs: {', '.join(SCENARIO_SLUGS)}"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing cache files instead of skipping them.",
    )
    return parser.parse_args()


def compute_group(
    name: str,
    scenarios,
    bin_type: str,
    output_dir: Path,
    scenario_slug: str | None = None,
    force: bool = False,
) -> None:
    from binner_sims import ffp10_binner_phiT

    output_dir.mkdir(parents=True, exist_ok=True)

    valid_slugs = {slug for _, _, _, slug in scenarios}
    if scenario_slug is not None and scenario_slug not in valid_slugs:
        raise ValueError(f"Unknown scenario slug {scenario_slug!r} for {name}. Valid: {sorted(valid_slugs)}")

    # Use the first scenario in the group for the fiducial curve and bin centers.
    fid_target = output_dir / f"{name}_fiducial.npz"
    if fid_target.exists() and not force:
        print(f"Skipping existing {fid_target}")
        ell = np.load(fid_target, allow_pickle=True)["ell"]
    else:
        b0 = ffp10_binner_phiT(scenarios[0][2], scenarios[0][0], bin_type)
        cl_fid = b0.fiducial_cl_scaled(False)
        ell_full = np.arange(len(cl_fid))
        ell = b0.bin_lavs
        np.savez(
            fid_target,
            ell_full=ell_full,
            cl_fid=cl_fid,
            ell=ell,
            bin_type=bin_type,
            group=name,
        )
        print(f"Wrote {fid_target}")

    for parfile, label, estimator, slug in scenarios:
        if scenario_slug is not None and slug != scenario_slug:
            continue
        target = output_dir / f"{name}_{slug}.npz"
        if target.exists() and not force:
            print(f"Skipping existing {target}")
            continue
        print(f"Computing {name}: {label} [{estimator}] from {parfile.TEMP}")
        binner = ffp10_binner_phiT(estimator, parfile, bin_type)
        cl_mean, cl_err = binner.get_cL_PHI_T_with_error(scaled=True)
        np.savez(
            target,
            ell=ell,
            cl_mean=cl_mean,
            cl_err=cl_err,
            label=label,
            estimator=estimator,
            temp=parfile.TEMP,
            bin_type=bin_type,
            group=name,
            slug=slug,
        )
        print(f"Wrote {target}")


def main() -> None:
    args = parse_args()
    ctx = load_scenarios()
    repo_root = Path(__file__).resolve().parent
    output_dir = Path(args.output_dir) if args.output_dir else repo_root / "THESIS" / "cache" / "pt_results"

    if args.group in ("noiseless", "both"):
        compute_group(
            "noiseless",
            ctx["noiseless"],
            args.bin_type,
            output_dir,
            scenario_slug=args.scenario,
            force=args.force,
        )
    if args.group in ("noisy", "both"):
        compute_group(
            "noisy",
            ctx["noisy"],
            args.bin_type,
            output_dir,
            scenario_slug=args.scenario,
            force=args.force,
        )


if __name__ == "__main__":
    main()
